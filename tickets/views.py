# tickets/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .forms import TicketForm
from .models import Ticket, Department, TicketReply

# Try to import optional models
try:
    from .models import Announcement, KnowledgeBase
    HAS_ANNOUNCEMENT = True
    HAS_KB = True
except ImportError:
    HAS_ANNOUNCEMENT = False
    HAS_KB = False

# View untuk login user
def user_login(request):
    # Jika user sudah login, redirect ke dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if not remember_me:
                # Jika tidak remember me, session akan expire ketika browser ditutup
                request.session.set_expiry(0)
            else:
                # Jika remember me, session akan expire dalam 2 minggu
                request.session.set_expiry(1209600)  # 2 weeks
            
            # Check if next parameter exists (redirect after login)
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, 'Username atau password salah. Silakan coba lagi.')
    
    return render(request, 'tickets/login.html')

# View untuk logout user
def user_logout(request):
    logout(request)
    messages.success(request, 'Anda telah berhasil logout.')
    return redirect('login')

# View Dashboard dengan statistik lengkap
@login_required
def dashboard(request):
    user = request.user
    
    # Get user's tickets
    user_tickets = Ticket.objects.filter(created_by=user)
    
    # Calculate statistics
    total_tickets = user_tickets.count()
    active_tickets = user_tickets.filter(status__in=['OPEN', 'IN_PROGRESS']).count()
    open_tickets = user_tickets.filter(status='OPEN').count()
    in_progress_tickets = user_tickets.filter(status='IN_PROGRESS').count()
    closed_tickets = user_tickets.filter(status='CLOSED').count()
    
    # Calculate average response time (from ticket creation to first reply)
    tickets_with_replies = user_tickets.annotate(
        reply_count=Count('replies')
    ).filter(reply_count__gt=0)
    
    avg_response_time = None
    if tickets_with_replies.exists():
        total_response_time = timedelta()
        count = 0
        for ticket in tickets_with_replies:
            first_reply = ticket.replies.order_by('created_at').first()
            if first_reply:
                response_time = first_reply.created_at - ticket.created_at
                total_response_time += response_time
                count += 1
        
        if count > 0:
            avg_seconds = total_response_time.total_seconds() / count
            avg_hours = avg_seconds / 3600
            if avg_hours < 1:
                avg_response_time = f"{int(avg_seconds / 60)}m"
            else:
                avg_response_time = f"{avg_hours:.1f}h"
    
    if not avg_response_time:
        avg_response_time = "N/A"
    
    # Get recent tickets (last 3)
    recent_tickets = user_tickets.order_by('-updated_at')[:3]
    
    # Get active announcements - cek dulu apakah model ada
    try:
        active_announcements = Announcement.objects.filter(
            is_active=True
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )[:2]
    except:
        active_announcements = []
    
    # Get popular knowledge base articles - cek dulu apakah model ada
    try:
        popular_articles = KnowledgeBase.objects.filter(is_published=True)[:3]
    except:
        popular_articles = []
    
    # Check for unread notifications (tickets with new replies)
    unread_count = 0
    for ticket in user_tickets.filter(status__in=['OPEN', 'IN_PROGRESS']):
        try:
            last_reply = ticket.get_last_reply()
            if last_reply and last_reply.user != user:
                unread_count += 1
        except:
            pass
    
    context = {
        'total_tickets': total_tickets,
        'active_tickets': active_tickets,
        'open_tickets': open_tickets,
        'in_progress_tickets': in_progress_tickets,
        'closed_tickets': closed_tickets,
        'avg_response_time': avg_response_time,
        'recent_tickets': recent_tickets,
        'announcements': active_announcements,
        'popular_articles': popular_articles,
        'unread_count': unread_count,
    }
    
    return render(request, 'tickets/dashboard.html', context)

# View untuk halaman daftar semua tiket user
@login_required
def my_tickets(request):
    user = request.user
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    tickets = Ticket.objects.filter(created_by=user)
    
    # Apply filters
    if status_filter != 'all':
        tickets = tickets.filter(status=status_filter.upper())
    
    if priority_filter != 'all':
        tickets = tickets.filter(priority=priority_filter.upper())
    
    if search_query:
        tickets = tickets.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Order by most recent
    tickets = tickets.order_by('-updated_at')
    
    context = {
        'tickets': tickets,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search_query': search_query,
    }
    
    return render(request, 'tickets/my_tickets.html', context)

# View untuk detail tiket dengan balasan
@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, created_by=request.user)
    replies = ticket.replies.all().order_by('created_at')
    
    # Handle new reply from user
    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            TicketReply.objects.create(
                ticket=ticket,
                user=request.user,
                message=message
            )
            messages.success(request, 'Balasan Anda telah dikirim.')
            return redirect('ticket-detail', ticket_id=ticket.id)
    
    context = {
        'ticket': ticket,
        'replies': replies,
    }
    
    return render(request, 'tickets/ticket_detail.html', context)

# View untuk halaman sukses
@login_required
def ticket_success(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, created_by=request.user)
    return render(request, 'tickets/ticket_success.html', {
        'ticket': ticket
    })

# View untuk halaman "Kirim Tiket"
@login_required
def create_ticket(request):
    user = request.user 

    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            new_ticket = form.save(commit=False) 
            new_ticket.created_by = user 
            new_ticket.save() 
            
            recipient_email = form.cleaned_data['reply_to_email'] 
            
            try:
                subject = f"[Ticket ID: {new_ticket.id}] {new_ticket.title}"
                message = (
                    f"Halo {new_ticket.created_by.username},\n\n"
                    f"Terima kasih telah menghubungi kami. Tiket Anda telah berhasil dibuat dengan rincian berikut:\n\n"
                    f"ID Tiket: {new_ticket.id}\n"
                    f"Judul: {new_ticket.title}\n"
                    f"Departemen: {new_ticket.department.name if new_ticket.department else 'Tidak ditentukan'}\n"
                    f"Prioritas: {new_ticket.get_priority_display()}\n"
                    f"Status: {new_ticket.get_status_display()}\n\n"
                    f"Deskripsi:\n{new_ticket.description}\n\n"
                    f"---\n"
                    f"Tim support kami akan segera meninjau tiket Anda dan memberikan balasan. "
                    f"Mohon menunggu balasan dari tim support melalui email ini.\n\n"
                    f"Jika Anda memiliki pertanyaan lebih lanjut, silakan hubungi kami.\n\n"
                    f"Salam,\nTim Support"
                )
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient_email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending confirmation email: {e}")
            
            messages.success(request, f'Tiket #{new_ticket.id} berhasil dibuat!')
            return redirect('ticket-success', ticket_id=new_ticket.id)
    
    else:
        if not Department.objects.exists():
            return render(request, 'tickets/setup_error.html')

        # Siapkan data awal untuk form
        initial_data = {
            'reply_to_email': user.email 
        }
        form = TicketForm(initial=initial_data)

    context = {
        'form': form,
        'user': user 
    }
    return render(request, 'tickets/create_ticket.html', context)

# View untuk Knowledge Base list
@login_required
def knowledge_base_list(request):
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', 'all')
    
    articles = KnowledgeBase.objects.filter(is_published=True)
    
    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(category__icontains=search_query)
        )
    
    if category_filter != 'all':
        articles = articles.filter(category=category_filter)
    
    # Get all categories
    categories = KnowledgeBase.objects.filter(
        is_published=True
    ).values_list('category', flat=True).distinct()
    
    context = {
        'articles': articles,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter,
    }
    
    return render(request, 'tickets/knowledge_base_list.html', context)

# View untuk Knowledge Base detail
@login_required
def knowledge_base_detail(request, article_id):
    article = get_object_or_404(KnowledgeBase, id=article_id, is_published=True)
    article.increment_views()
    
    # Get related articles
    related_articles = KnowledgeBase.objects.filter(
        category=article.category,
        is_published=True
    ).exclude(id=article.id)[:3]
    
    context = {
        'article': article,
        'related_articles': related_articles,
    }
    
    return render(request, 'tickets/knowledge_base_detail.html', context)

# View untuk halaman pengaturan user
@login_required
def user_settings(request):
    if request.method == 'POST':
        # Update user profile
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        messages.success(request, 'Profil berhasil diperbarui!')
        return redirect('user-settings')
    
    return render(request, 'tickets/user_settings.html')

# View untuk halaman announcements
@login_required
def announcements_list(request):
    announcements = Announcement.objects.filter(
        is_active=True
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
    )
    
    context = {
        'announcements': announcements,
    }
    
    return render(request, 'tickets/announcements_list.html', context)