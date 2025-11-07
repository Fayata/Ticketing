# tickets/models.py
from django.db import models
from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

# Tabel untuk menyimpan Pilihan Departemen
class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# Tabel utama untuk menyimpan data Tiket
class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        CLOSED = 'CLOSED', 'Closed'
    
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'

    title = models.CharField(max_length=255)
    description = models.TextField()
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, null=True, blank=True)
    
    # Field baru untuk menyimpan email balasan
    reply_to_email = models.EmailField(max_length=254, blank=True)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.status}] #{self.id} {self.title}"

# Tabel untuk menyimpan balasan-balasan di setiap tiket
class TicketReply(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.user.username} on {self.ticket.title}"

    # Kustomisasi fungsi 'save'
    def save(self, *args, **kwargs):
        is_new = not self.pk 
        super().save(*args, **kwargs)

        # Kirim email hanya jika reply baru dan bukan dari pembuat ticket
        if is_new and self.user != self.ticket.created_by:
            recipient_email = self.ticket.reply_to_email

            if not recipient_email:
                recipient_email = self.ticket.created_by.email

            # Pastikan ada email recipient
            if not recipient_email:
                logger.error(f"Tidak ada email untuk ticket {self.ticket.id}. User: {self.ticket.created_by.username}")
                return

            try:
                subject = f"RE: [Ticket ID: {self.ticket.id}] {self.ticket.title}"
                email_message = (
                    f"Halo {self.ticket.created_by.username},\n\n"
                    f"Tim support kami ({self.user.get_full_name() or self.user.username}) telah membalas tiket Anda:\n\n"
                    f"---\n"
                    f"{self.message}\n"
                    f"---\n\n"
                    f"Detail Tiket:\n"
                    f"ID Tiket: {self.ticket.id}\n"
                    f"Judul: {self.ticket.title}\n"
                    f"Status: {self.ticket.get_status_display()}\n\n"
                    f"Jika Anda ingin memberikan tanggapan atau informasi tambahan, "
                    f"silakan balas email ini atau hubungi tim support kami.\n\n"
                    f"Salam,\n"
                    f"{self.user.get_full_name() or self.user.username}\n"
                    f"Tim Support"
                )
                
                logger.info(f"Mengirim email balasan ticket {self.ticket.id} ke {recipient_email}")
                logger.info(f"Subject: {subject}")
                logger.info(f"From: {settings.DEFAULT_FROM_EMAIL}")
                
                send_mail(
                    subject,
                    email_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient_email],
                    fail_silently=False,
                )
                
                logger.info(f"Email berhasil dikirim ke {recipient_email}")
                
            except Exception as e:
                error_msg = f"Error sending reply email untuk ticket {self.ticket.id}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                print(error_msg)
        else:
            if is_new:
                logger.info(f"Reply tidak mengirim email karena user yang sama (user: {self.user.username}, created_by: {self.ticket.created_by.username})")