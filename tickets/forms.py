# tickets/forms.py
from django import forms
from .models import Ticket

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