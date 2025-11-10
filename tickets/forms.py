# tickets/forms.py
from django import forms
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.contrib.auth import get_user_model
from .models import Ticket

User = get_user_model()

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'department', 'priority', 'reply_to_email', 'description']
        labels = {
            'reply_to_email': 'Alamat Email *',
        }

        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

class UserProfileForm(forms.ModelForm):
    """Form untuk mengubah username dan email"""
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        labels = {
            'username': 'Username',
            'email': 'Alamat Email',
            'first_name': 'Nama Depan',
            'last_name': 'Nama Belakang',
        }
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Masukkan username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Masukkan email'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Masukkan nama depan'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Masukkan nama belakang'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Username tidak bisa diubah jika sudah digunakan oleh user lain
        self.fields['username'].help_text = 'Wajib diisi. Hanya huruf, angka, dan @/./+/-/_ yang diperbolehkan.'

class CustomPasswordChangeForm(PasswordChangeForm):
    """Form untuk mengubah password"""
    old_password = forms.CharField(
        label='Password Lama',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Masukkan password lama'
        }),
        strip=False,
    )
    new_password1 = forms.CharField(
        label='Password Baru',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Masukkan password baru'
        }),
        strip=False,
        help_text='Minimal 8 karakter, tidak boleh terlalu mirip dengan informasi pribadi Anda.',
    )
    new_password2 = forms.CharField(
        label='Konfirmasi Password Baru',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Konfirmasi password baru'
        }),
        strip=False,
    )