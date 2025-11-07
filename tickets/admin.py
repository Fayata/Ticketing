# tickets/admin.py
from django.contrib import admin
from .models import Ticket, TicketReply, Department

# Tampilkan balasan langsung di bawah halaman detail Tiket
class TicketReplyInline(admin.TabularInline):
    model = TicketReply
    extra = 1  # Tampilkan 1 form kosong untuk membuat reply baru
    fields = ('message', 'user', 'created_at')
    readonly_fields = ('created_at', 'user')  # created_at dan user readonly (user otomatis diisi)
    can_delete = False
    verbose_name = "Balasan"
    verbose_name_plural = "Balasan"
    
    def get_readonly_fields(self, request, obj=None):
        # user dan created_at selalu readonly
        # user akan otomatis diisi dengan admin yang sedang login di save_formset
        return ('created_at', 'user')

# Kustomisasi tampilan list Tiket di admin
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'priority', 'created_by', 'department', 'created_at')
    list_filter = ('status', 'priority', 'department', 'created_at')
    search_fields = ('title', 'description', 'created_by__username', 'created_by__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [TicketReplyInline]  # Terapkan inline di atas
    
    fieldsets = (
        ('Informasi Tiket', {
            'fields': ('title', 'description', 'status', 'priority', 'department')
        }),
        ('Informasi Pengguna', {
            'fields': ('created_by', 'reply_to_email')
        }),
        ('Timestamp', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_formset(self, request, form, formset, change):
        """
        Override untuk auto-set user ketika membuat reply baru di admin
        """
        if formset.model == TicketReply:
            instances = formset.save(commit=False)
            for instance in instances:
                # Jika membuat reply baru, set user ke admin yang sedang login
                if not instance.pk:
                    instance.user = request.user
                    instance.ticket = form.instance  # Set ticket dari parent form
                instance.save()
            formset.save_m2m()
        else:
            # Untuk formset lainnya, gunakan default behavior
            super().save_formset(request, form, formset, change)

# Custom admin untuk TicketReply (jika dibuat langsung, bukan melalui inline)
class TicketReplyAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('ticket__title', 'user__username', 'message')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Informasi Balasan', {
            'fields': ('ticket', 'user', 'message')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Jika membuat reply baru, auto-set user ke admin yang sedang login
        if not change:  # Jika baru dibuat (bukan edit)
            obj.user = request.user
        super().save_model(request, obj, form, change)

# Daftarkan model dan kustomisasinya ke admin
admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketReply, TicketReplyAdmin)
admin.site.register(Department)