# tickets/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import TicketForm
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
    # Nanti kita bisa tambahkan logika untuk menampilkan daftar tiket user
    return render(request, 'tickets/dashboard.html')
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