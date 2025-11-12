# tickets/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from .forms import TicketForm, UserProfileForm, CustomPasswordChangeForm
from .models import Ticket, Department

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
            # Check both GET and POST for next parameter
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

# View baru untuk Dashboard
@login_required
def dashboard(request):
    user = request.user
    # Ambil semua tiket user
    user_tickets = Ticket.objects.filter(created_by=user).order_by('-created_at')
    
    waiting_tickets = user_tickets.filter(status='WAITING').count() 
    in_progress_tickets = user_tickets.filter(status='IN_PROGRESS').count()
    closed_tickets = user_tickets.filter(status='CLOSED').count()
    # 2. Tambahkan hitungan total tiket
    total_tickets = user_tickets.count()
    
    # Ambil tiket terbaru (limit 5)
    recent_tickets = user_tickets[:5]
    
    context = {
        'waiting_tickets': waiting_tickets,
        'in_progress_tickets': in_progress_tickets,
        'closed_tickets': closed_tickets,
        'total_tickets': total_tickets,
        'recent_tickets': recent_tickets,
        'unread_count': 0, 
        'announcements': [],  
        'popular_articles': [],  
    }
    return render(request, 'tickets/dashboard.html', context)
@login_required
def ticket_success(request, ticket_id):
    # Ambil data tiket untuk ditampilkan ID-nya
    ticket = get_object_or_404(Ticket, id=ticket_id)
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
            # Email balasan sudah otomatis tersimpan dari form
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
                    [recipient_email],  # Gunakan email dari form
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending confirmation email: {e}")
            
            return redirect('ticket-success', ticket_id=new_ticket.id)
    
    else:
        if not Department.objects.exists():
            return render(request, 'tickets/setup_error.html')

        # --- UPDATE LOGIKA INITIAL DATA ---
        # Siapkan data awal untuk form
        initial_data = {
            'reply_to_email': user.email 
        }
        # Masukkan data awal ke form
        form = TicketForm(initial=initial_data)

    context = {
        'form': form,
        'user': user 
    }
    return render(request, 'tickets/create_ticket.html', context)

# View untuk Settings/Profile User
@login_required
def user_settings(request):
    user = request.user
    
    # Handle profile update
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = UserProfileForm(request.POST, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profil Anda berhasil diperbarui!')
                return redirect('user-settings')
            else:
                messages.error(request, 'Terjadi kesalahan saat memperbarui profil. Silakan periksa form Anda.')
        elif 'change_password' in request.POST:
            password_form = CustomPasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Penting untuk tidak logout user
                messages.success(request, 'Password Anda berhasil diubah!')
                return redirect('user-settings')
            else:
                messages.error(request, 'Terjadi kesalahan saat mengubah password. Silakan periksa form Anda.')
        else:
            profile_form = UserProfileForm(instance=user)
            password_form = CustomPasswordChangeForm(user)
    else:
        profile_form = UserProfileForm(instance=user)
        password_form = CustomPasswordChangeForm(user)
    
    context = {
        'profile_form': profile_form,
        'password_form': password_form,
        'user': user,
    }
    return render(request, 'tickets/settings.html', context)

# View untuk My Tickets (daftar semua tiket user)
@login_required
def my_tickets(request):
    user = request.user
    
    # Ambil semua tiket user
    tickets = Ticket.objects.filter(created_by=user).order_by('-created_at')
    
    # Filter berdasarkan search query
    search_query = request.GET.get('search', '')
    if search_query:
        # Coba konversi ke integer untuk pencarian ID
        try:
            ticket_id = int(search_query)
            tickets = tickets.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(id=ticket_id)
            )
        except ValueError:
            # Jika bukan angka, cari berdasarkan title dan description saja
            tickets = tickets.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
    
    # Filter berdasarkan status
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        if status_filter == 'open':
            tickets = tickets.filter(status='OPEN')
        elif status_filter == 'in_progress':
            tickets = tickets.filter(status='IN_PROGRESS')
        elif status_filter == 'closed':
            tickets = tickets.filter(status='CLOSED')
    
    # Filter berdasarkan prioritas
    priority_filter = request.GET.get('priority', 'all')
    if priority_filter != 'all':
        tickets = tickets.filter(priority=priority_filter.upper())
    
    context = {
        'tickets': tickets,
        'search_query': search_query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
    }
    return render(request, 'tickets/my_tickets.html', context)

# View untuk Ticket Detail
@login_required
def ticket_detail(request, ticket_id):
    user = request.user
    ticket = get_object_or_404(Ticket, id=ticket_id, created_by=user)
    
    # Ambil semua replies untuk ticket ini
    replies = ticket.replies.all().order_by('created_at')
    
    # Handle reply form
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        if message:
            from .models import TicketReply
            reply = TicketReply.objects.create(
                ticket=ticket,
                user=user,
                message=message
            )
            messages.success(request, 'Balasan Anda berhasil dikirim!')
            return redirect('ticket-detail', ticket_id=ticket.id)
        else:
            messages.error(request, 'Pesan tidak boleh kosong.')
    
    context = {
        'ticket': ticket,
        'replies': replies,
    }
    return render(request, 'tickets/ticket_detail.html', context)