# tickets/admin.py
from django.contrib import admin
from .models import Ticket, TicketReply, Department

# Tampilkan balasan langsung di bawah halaman detail Tiket
class TicketReplyInline(admin.TabularInline):
    model = TicketReply
    extra = 1
    fields = ('message', 'user', 'created_at')
    readonly_fields = ('created_at', 'user') 
    can_delete = False
    verbose_name = "Balasan"
    verbose_name_plural = "Balasan"
    
    def get_readonly_fields(self, request, obj=None):
        return ('created_at', 'user')

# Kustomisasi tampilan list Tiket di admin
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'priority', 'created_by', 'department', 'created_at')
    list_filter = ('status', 'priority', 'department', 'created_at')
    search_fields = ('title', 'description', 'created_by__username', 'created_by__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [TicketReplyInline]
    
    list_editable = ('status', 'priority')

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
                if not instance.pk:
                    instance.user = request.user
                    instance.ticket = form.instance 
                instance.save()
            formset.save_m2m()
        else:
            super().save_formset(request, form, formset, change)

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
        if not change:  
            obj.user = request.user
        super().save_model(request, obj, form, change)

admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketReply, TicketReplyAdmin)
admin.site.register(Department)