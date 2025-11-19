# tickets/urls.py
from django.urls import path
from django.shortcuts import redirect
from . import views

def redirect_to_login(request):
    """Redirect root URL to login page"""
    return redirect('login')

urlpatterns = [
    # Root URL redirect ke login
    path('', redirect_to_login, name='home'),
    
    # Halaman Login (custom view untuk user)
    path('login/', views.user_login, name='login'),
    # Halaman Registrasi user portal
    path('register/', views.user_register, name='register'),
    
    # Halaman Logout (custom view yang menerima GET request)
    path('logout/', views.user_logout, name='logout'),
    
    # Halaman Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Halaman Daftar Tiket
    path('tiket/', views.my_tickets, name='my-tickets'),
    
    # Halaman Detail Tiket
    path('tiket/<int:ticket_id>/', views.ticket_detail, name='ticket-detail'),
    
    # Halaman Form Kirim Tiket
    path('kirim-tiket/', views.create_ticket, name='create-ticket'),
    
    # Halaman Sukses
    path('tiket/sukses/<int:ticket_id>/', views.ticket_success, name='ticket-success'),

    path('settings/', views.user_settings, name='user-settings'),
]