from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path, reverse
import csv
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from django.contrib import messages
from django.db import models as db_models
from django.forms import DateTimeInput
from .models import (
    Category, Article, CommonForm,
    ConnectionRequest, BillPayment, Complaint,
    PowerOutage, MeterReading, FAQ, SupportTicket, TicketReply
)
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group


def export_to_csv(modeladmin, request, queryset):
    """Export selected items to CSV"""
    opts = modeladmin.model._meta
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={opts.verbose_name}.csv'
    
    writer = csv.writer(response)
    fields = [field for field in opts.get_fields() if not field.many_to_many and not field.one_to_many]
    
    # Write headers
    writer.writerow([field.verbose_name for field in fields])
    
    # Write data
    for obj in queryset:
        row = [getattr(obj, field.name) for field in fields]
        writer.writerow(row)
    
    return response

export_to_csv.short_description = "Export to CSV"


# ── FEATURE 5: Bulk Actions ────────────────────────────────────────────────

def mark_approved(modeladmin, request, queryset):
    for obj in queryset:
        obj.status = 'approved'
        obj.save()
mark_approved.short_description = "✅ Mark selected as Approved"

def mark_rejected(modeladmin, request, queryset):
    for obj in queryset:
        obj.status = 'rejected'
        obj.save()
mark_rejected.short_description = "❌ Mark selected as Rejected"

def mark_completed(modeladmin, request, queryset):
    for obj in queryset:
        obj.status = 'completed'
        obj.save()
mark_completed.short_description = "🎉 Mark selected as Completed"

def mark_in_progress(modeladmin, request, queryset):
    for obj in queryset:
        obj.status = 'in_progress'
        obj.save()
mark_in_progress.short_description = "🔧 Mark selected as In Progress"

def mark_resolved(modeladmin, request, queryset):
    for obj in queryset:
        obj.status = 'resolved'
        obj.save()
mark_resolved.short_description = "✅ Mark selected as Resolved"

def mark_payment_completed(modeladmin, request, queryset):
    from django.utils import timezone
    for obj in queryset:
        obj.payment_status = 'completed'
        obj.payment_date = timezone.now()
        obj.save()
mark_payment_completed.short_description = "✅ Mark payments as Completed"

def mark_payment_failed(modeladmin, request, queryset):
    for obj in queryset:
        obj.payment_status = 'failed'
        obj.save()
mark_payment_failed.short_description = "❌ Mark payments as Failed"

def mark_meter_verified(modeladmin, request, queryset):
    for obj in queryset:
        obj.status = 'verified'
        obj.save()
mark_meter_verified.short_description = "✅ Verify selected meter readings"

def mark_meter_rejected(modeladmin, request, queryset):
    for obj in queryset:
        obj.status = 'rejected'
        obj.save()
mark_meter_rejected.short_description = "❌ Reject selected meter readings"

def mark_ticket_resolved(modeladmin, request, queryset):
    for obj in queryset:
        obj.status = 'resolved'
        obj.save()
mark_ticket_resolved.short_description = "✅ Mark tickets as Resolved"

def mark_ticket_closed(modeladmin, request, queryset):
    for obj in queryset:
        obj.status = 'closed'
        obj.save()
mark_ticket_closed.short_description = "🔒 Close selected tickets"

def send_reminder_email(modeladmin, request, queryset):
    """Send a reminder email to all selected users"""
    from myapp.utils import send_email
    count = 0
    for obj in queryset:
        try:
            email = getattr(obj, 'email', None) or getattr(obj.user, 'email', None)
            ref = getattr(obj, 'complaint_number', None) or getattr(obj, 'request_number', None) or getattr(obj, 'ticket_number', None) or str(obj.pk)
            if email:
                send_email(
                    subject='PowerGrid — Your Application is Pending',
                    message=f"Dear Customer,\n\nThis is a reminder that your application {ref} is still pending review.\n\nPlease log in to check the status.\n\nBest regards,\nPowerGrid Team",
                    recipient_list=[email],
                )
                count += 1
        except Exception:
            pass
    modeladmin.message_user(request, f"Reminder sent to {count} user(s).")
send_reminder_email.short_description = "📧 Send reminder email to selected users"



# MAKE SURE ConnectionRequest is NOT registered anywhere before this point
# Unregister if already registered (safety check)
if admin.site.is_registered(ConnectionRequest):
    admin.site.unregister(ConnectionRequest)

# NOW register it ONCE
@admin.register(ConnectionRequest)
class ConnectionRequestAdmin(ModelAdmin):
    list_display = ['request_number', 'full_name', 'connection_type', 'status_badge', 'created_at', 'quick_actions']
    list_filter = ['status', 'connection_type', 'created_at']
    search_fields = ['request_number', 'full_name', 'phone', 'email']
    readonly_fields = ['request_number', 'created_at', 'updated_at']
    formfield_overrides = {
        db_models.DateTimeField: {'widget': DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M')},
    }
    actions = [export_to_csv, mark_approved, mark_rejected, mark_completed, mark_in_progress, send_reminder_email]
    
    fieldsets = [
        ('Request Information', {
            'fields': ['request_number', 'user', 'status', 'created_at', 'updated_at']
        }),
        ('Applicant Details', {
            'fields': ['full_name', 'phone', 'email', 'alternate_phone']
        }),
        ('Address', {
            'fields': ['address_line1', 'address_line2', 'city', 'state', 'pincode', 'landmark']
        }),
        ('Connection Details', {
            'fields': ['connection_type', 'estimated_load', 'purpose']
        }),
        ('Property Details', {
            'fields': ['property_ownership', 'property_type']
        }),
        ('Documents', {
            'fields': ['id_proof', 'address_proof', 'property_document']
        }),
        ('Admin Actions', {
            'fields': ['assigned_to', 'admin_remarks', 'rejection_reason', 'inspection_date', 'completion_date']
        }),
    ]
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'under_review': '#2196F3',
            'site_inspection': '#9C27B0',
            'approved': '#4CAF50',
            'rejected': '#F44336',
            'completed': '#00BCD4',
        }
        color = colors.get(obj.status, '#999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('<int:pk>/approve/', self.admin_site.admin_view(self.approve_view), name='connectionrequest_approve'),
            path('<int:pk>/reject/',  self.admin_site.admin_view(self.reject_view),  name='connectionrequest_reject'),
        ]
        return custom + urls

    def approve_view(self, request, pk):
        obj = ConnectionRequest.objects.get(pk=pk)
        obj.status = 'approved'
        obj.save()
        messages.success(request, f'✅ {obj.request_number} approved.')
        return HttpResponseRedirect(reverse('admin:myapp_connectionrequest_changelist'))

    def reject_view(self, request, pk):
        obj = ConnectionRequest.objects.get(pk=pk)
        obj.status = 'rejected'
        obj.save()
        messages.success(request, f'❌ {obj.request_number} rejected.')
        return HttpResponseRedirect(reverse('admin:myapp_connectionrequest_changelist'))

    def quick_actions(self, obj):
        approve_url = reverse('admin:connectionrequest_approve', args=[obj.pk])
        reject_url  = reverse('admin:connectionrequest_reject',  args=[obj.pk])
        return format_html(
            '<a href="{}" style="background:#3a9e25;color:#fff;padding:4px 10px;border-radius:6px;'
            'font-size:0.75rem;font-weight:700;text-decoration:none;margin-right:4px;"'
            ' onclick="return confirm(\'Approve this request?\')">✅ Approve</a>'
            '<a href="{}" style="background:#e53e3e;color:#fff;padding:4px 10px;border-radius:6px;'
            'font-size:0.75rem;font-weight:700;text-decoration:none;"'
            ' onclick="return confirm(\'Reject this request?\')">❌ Reject</a>',
            approve_url, reject_url
        )
    quick_actions.short_description = 'Quick Actions'
    quick_actions.allow_tags = True


# Do the same for all other models
if admin.site.is_registered(CommonForm):
    admin.site.unregister(CommonForm)

@admin.register(CommonForm)
class CommonFormAdmin(ModelAdmin):
    list_display = ['form_number', 'name', 'phone', 'email', 'status_badge', 'priority_badge', 'submitted_date']
    list_filter = ['status', 'priority', 'submitted_date']
    search_fields = ['form_number', 'name', 'phone', 'email', 'address']
    readonly_fields = ['form_number', 'submitted_date', 'updated_date']
    
    fieldsets = [
        ('Form Information', {
            'fields': ['form_number', 'submitted_date', 'updated_date']
        }),
        ('Applicant Details', {
            'fields': ['name', 'phone', 'email', 'address']
        }),
        ('Form Details', {
            'fields': ['subject', 'description']
        }),
        ('Status & Assignment', {
            'fields': ['status', 'priority', 'assigned_to', 'remarks']
        }),
    ]
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'under_review': '#2196F3',
            'approved': '#4CAF50',
            'rejected': '#F44336',
            'completed': '#9C27B0',
        }
        color = colors.get(obj.status, '#999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def priority_badge(self, obj):
        colors = {
            'low': '#4CAF50',
            'medium': '#FF9800',
            'high': '#FF5722',
            'urgent': '#F44336',
        }
        color = colors.get(obj.priority, '#999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'


if admin.site.is_registered(Category):
    admin.site.unregister(Category)

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']


if admin.site.is_registered(Article):
    admin.site.unregister(Article)

@admin.register(Article)
class ArticleAdmin(ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'published_date']
    list_filter = ['status', 'category', 'published_date']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_date'
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['title', 'slug', 'author', 'category']
        }),
        ('Content', {
            'fields': ['content', 'status']
        }),
        ('Publishing', {
            'fields': ['published_date']
        }),
    ]


if admin.site.is_registered(BillPayment):
    admin.site.unregister(BillPayment)

@admin.register(BillPayment)
class BillPaymentAdmin(ModelAdmin):
    list_display = ['payment_id', 'consumer_number', 'billing_month', 'paid_amount', 'payment_status_badge', 'payment_date']
    list_filter = ['payment_status', 'payment_method', 'created_at']
    search_fields = ['payment_id', 'consumer_number', 'transaction_id']
    readonly_fields = ['payment_id', 'created_at', 'updated_at']
    formfield_overrides = {
        db_models.DateTimeField: {'widget': DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M')},
    }
    actions = [export_to_csv, mark_payment_completed, mark_payment_failed]
    list_display = ['payment_id', 'consumer_number', 'billing_month', 'paid_amount', 'payment_status_badge', 'payment_date', 'quick_payment_actions']
    
    fieldsets = [
        ('Payment Information', {
            'fields': ['payment_id', 'user', 'consumer_number', 'billing_month']
        }),
        ('Amount Details', {
            'fields': ['bill_amount', 'paid_amount', 'late_fee', 'discount']
        }),
        ('Payment Details', {
            'fields': ['payment_method', 'payment_status', 'transaction_id', 'payment_date']
        }),
        ('Additional', {
            'fields': ['remarks', 'receipt_generated', 'created_at', 'updated_at']
        }),
    ]
    
    def payment_status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'processing': '#2196F3',
            'completed': '#4CAF50',
            'failed': '#F44336',
            'refunded': '#9C27B0',
        }
        color = colors.get(obj.payment_status, '#999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'Status'

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('<int:pk>/complete/', self.admin_site.admin_view(self.complete_view), name='billpayment_complete'),
            path('<int:pk>/fail/',     self.admin_site.admin_view(self.fail_view),     name='billpayment_fail'),
        ]
        return custom + urls

    def complete_view(self, request, pk):
        from django.utils import timezone
        obj = BillPayment.objects.get(pk=pk)
        obj.payment_status = 'completed'
        obj.payment_date = timezone.now()
        obj.save()
        messages.success(request, f'✅ Payment {obj.payment_id} marked completed.')
        return HttpResponseRedirect(reverse('admin:myapp_billpayment_changelist'))

    def fail_view(self, request, pk):
        obj = BillPayment.objects.get(pk=pk)
        obj.payment_status = 'failed'
        obj.save()
        messages.success(request, f'❌ Payment {obj.payment_id} marked failed.')
        return HttpResponseRedirect(reverse('admin:myapp_billpayment_changelist'))

    def quick_payment_actions(self, obj):
        if obj.payment_status in ('completed', 'failed', 'refunded'):
            return format_html('<span style="color:#999;font-size:0.78rem;">—</span>')
        complete_url = reverse('admin:billpayment_complete', args=[obj.pk])
        fail_url     = reverse('admin:billpayment_fail',     args=[obj.pk])
        return format_html(
            '<a href="{}" style="background:#3a9e25;color:#fff;padding:4px 10px;border-radius:6px;'
            'font-size:0.75rem;font-weight:700;text-decoration:none;margin-right:4px;"'
            ' onclick="return confirm(\'Mark payment as completed?\')">✅ Complete</a>'
            '<a href="{}" style="background:#e53e3e;color:#fff;padding:4px 10px;border-radius:6px;'
            'font-size:0.75rem;font-weight:700;text-decoration:none;"'
            ' onclick="return confirm(\'Mark payment as failed?\')">❌ Fail</a>',
            complete_url, fail_url
        )
    quick_payment_actions.short_description = 'Quick Actions'
    quick_payment_actions.allow_tags = True


if admin.site.is_registered(Complaint):
    admin.site.unregister(Complaint)

@admin.register(Complaint)
class ComplaintAdmin(ModelAdmin):
    list_display = ['complaint_number', 'full_name', 'category', 'status_badge', 'priority_badge', 'created_at', 'quick_actions']
    list_filter = ['status', 'priority', 'category', 'created_at']
    search_fields = ['complaint_number', 'full_name', 'phone', 'subject']
    readonly_fields = ['complaint_number', 'created_at', 'updated_at']
    formfield_overrides = {
        db_models.DateTimeField: {'widget': DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M')},
    }
    actions = [export_to_csv, mark_resolved, mark_in_progress, mark_rejected, send_reminder_email]
    
    fieldsets = [
        ('Complaint Information', {
            'fields': ['complaint_number', 'user', 'consumer_number', 'status', 'priority']
        }),
        ('Complainant Details', {
            'fields': ['full_name', 'phone', 'email']
        }),
        ('Complaint Details', {
            'fields': ['category', 'subject', 'description']
        }),
        ('Location', {
            'fields': ['address', 'landmark']
        }),
        ('Attachments', {
            'fields': ['attachment1', 'attachment2']
        }),
        ('Resolution', {
            'fields': ['assigned_to', 'resolution_details', 'resolved_date']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at']
        }),
    ]
    
    def status_badge(self, obj):
        colors = {
            'registered': '#FFA500',
            'acknowledged': '#2196F3',
            'in_progress': '#9C27B0',
            'resolved': '#4CAF50',
            'closed': '#607D8B',
            'reopened': '#FF9800',
        }
        color = colors.get(obj.status, '#999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def priority_badge(self, obj):
        colors = {
            'low': '#4CAF50',
            'medium': '#FF9800',
            'high': '#FF5722',
            'urgent': '#F44336',
        }
        color = colors.get(obj.priority, '#999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('<int:pk>/resolve/', self.admin_site.admin_view(self.resolve_view),    name='complaint_resolve'),
            path('<int:pk>/progress/', self.admin_site.admin_view(self.progress_view), name='complaint_progress'),
        ]
        return custom + urls

    def resolve_view(self, request, pk):
        obj = Complaint.objects.get(pk=pk)
        obj.status = 'resolved'
        obj.save()
        messages.success(request, f'✅ Complaint {obj.complaint_number} marked resolved.')
        return HttpResponseRedirect(reverse('admin:myapp_complaint_changelist'))

    def progress_view(self, request, pk):
        obj = Complaint.objects.get(pk=pk)
        obj.status = 'in_progress'
        obj.save()
        messages.success(request, f'🔧 Complaint {obj.complaint_number} marked in progress.')
        return HttpResponseRedirect(reverse('admin:myapp_complaint_changelist'))

    def quick_actions(self, obj):
        resolve_url  = reverse('admin:complaint_resolve',  args=[obj.pk])
        progress_url = reverse('admin:complaint_progress', args=[obj.pk])
        return format_html(
            '<a href="{}" style="background:#3a9e25;color:#fff;padding:4px 10px;border-radius:6px;'
            'font-size:0.75rem;font-weight:700;text-decoration:none;margin-right:4px;"'
            ' onclick="return confirm(\'Mark as Resolved?\')">✅ Resolve</a>'
            '<a href="{}" style="background:#2196F3;color:#fff;padding:4px 10px;border-radius:6px;'
            'font-size:0.75rem;font-weight:700;text-decoration:none;"'
            ' onclick="return confirm(\'Mark as In Progress?\')">🔧 Progress</a>',
            resolve_url, progress_url
        )
    quick_actions.short_description = 'Quick Actions'
    quick_actions.allow_tags = True


if admin.site.is_registered(PowerOutage):
    admin.site.unregister(PowerOutage)

@admin.register(PowerOutage)
class PowerOutageAdmin(ModelAdmin):
    list_display = ['report_number', 'area', 'outage_type', 'status_badge', 'outage_start_time', 'created_at']
    list_filter = ['status', 'outage_type', 'created_at']
    search_fields = ['report_number', 'area', 'full_name', 'consumer_number']
    readonly_fields = ['report_number', 'created_at', 'updated_at']
    formfield_overrides = {
        db_models.DateTimeField: {'widget': DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M')},
    }
    actions = [export_to_csv, mark_resolved, mark_in_progress]
    
    fieldsets = [
        ('Report Information', {
            'fields': ['report_number', 'user', 'status']
        }),
        ('Reporter Details', {
            'fields': ['full_name', 'phone', 'consumer_number']
        }),
        ('Outage Details', {
            'fields': ['outage_type', 'outage_start_time', 'outage_end_time', 'affected_households', 'description']
        }),
        ('Location', {
            'fields': ['area', 'address', 'landmark']
        }),
        ('Admin Actions', {
            'fields': ['assigned_to', 'cause', 'resolution_details', 'estimated_resolution_time']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at']
        }),
    ]
    
    def status_badge(self, obj):
        colors = {
            'reported': '#FFA500',
            'acknowledged': '#2196F3',
            'investigating': '#9C27B0',
            'repairing': '#FF9800',
            'resolved': '#4CAF50',
        }
        color = colors.get(obj.status, '#999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


if admin.site.is_registered(MeterReading):
    admin.site.unregister(MeterReading)

@admin.register(MeterReading)
class MeterReadingAdmin(ModelAdmin):
    list_display = ['reading_id', 'consumer_number', 'reading_date', 'units_consumed', 'status_badge', 'created_at', 'quick_meter_actions']
    list_filter = ['status', 'reading_date', 'created_at']
    search_fields = ['reading_id', 'consumer_number', 'meter_number']
    readonly_fields = ['reading_id', 'units_consumed', 'created_at', 'updated_at']
    actions = [export_to_csv, mark_meter_verified, mark_meter_rejected]
    
    fieldsets = [
        ('Reading Information', {
            'fields': ['reading_id', 'user', 'consumer_number', 'status']
        }),
        ('Reading Details', {
            'fields': ['reading_date', 'current_reading', 'previous_reading', 'units_consumed']
        }),
        ('Meter Details', {
            'fields': ['meter_number', 'meter_photo']
        }),
        ('Verification', {
            'fields': ['verified_by', 'verification_date', 'admin_remarks']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at']
        }),
    ]
    
    def status_badge(self, obj):
        colors = {
            'submitted': '#FFA500',
            'verified': '#4CAF50',
            'rejected': '#F44336',
            'billed': '#2196F3',
        }
        color = colors.get(obj.status, '#999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def quick_meter_actions(self, obj):
        if obj.status in ('verified', 'billed'):
            return format_html('<span style="color:#999;font-size:0.78rem;">—</span>')
        verify_url = reverse('admin:meterreading_verify', args=[obj.pk])
        reject_url = reverse('admin:meterreading_reject', args=[obj.pk])
        return format_html(
            '<a href="{}" style="background:#3a9e25;color:#fff;padding:4px 10px;border-radius:6px;'
            'font-size:0.75rem;font-weight:700;text-decoration:none;margin-right:4px;"'
            ' onclick="return confirm(\'Verify this reading?\')">✅ Verify</a>'
            '<a href="{}" style="background:#e53e3e;color:#fff;padding:4px 10px;border-radius:6px;'
            'font-size:0.75rem;font-weight:700;text-decoration:none;"'
            ' onclick="return confirm(\'Reject this reading?\')">❌ Reject</a>',
            verify_url, reject_url
        )
    quick_meter_actions.short_description = 'Quick Actions'
    quick_meter_actions.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('<int:pk>/verify/', self.admin_site.admin_view(self.verify_view), name='meterreading_verify'),
            path('<int:pk>/reject/', self.admin_site.admin_view(self.reject_view), name='meterreading_reject'),
        ]
        return custom + urls

    def verify_view(self, request, pk):
        from django.utils import timezone
        obj = MeterReading.objects.get(pk=pk)
        obj.status = 'verified'
        obj.verified_by = request.user
        obj.verification_date = timezone.now()
        obj.save()
        messages.success(request, f'✅ Meter reading {obj.reading_id} verified.')
        return HttpResponseRedirect(reverse('admin:myapp_meterreading_changelist'))

    def reject_view(self, request, pk):
        obj = MeterReading.objects.get(pk=pk)
        obj.status = 'rejected'
        obj.save()
        messages.success(request, f'❌ Meter reading {obj.reading_id} rejected.')
        return HttpResponseRedirect(reverse('admin:myapp_meterreading_changelist'))


if admin.site.is_registered(FAQ):
    admin.site.unregister(FAQ)

@admin.register(FAQ)
class FAQAdmin(ModelAdmin):
    list_display = ['question', 'category', 'order', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['question', 'answer']
    actions = [export_to_csv]
    
    fieldsets = [
        ('FAQ Details', {
            'fields': ['category', 'question', 'answer', 'order', 'is_active']
        }),
    ]


class TicketReplyInline(admin.TabularInline):
    model = TicketReply
    extra = 1
    fields = ['message', 'is_staff_reply', 'author']
    readonly_fields = []

    def get_extra(self, request, obj=None, **kwargs):
        return 1


if admin.site.is_registered(SupportTicket):
    admin.site.unregister(SupportTicket)

@admin.register(SupportTicket)
class SupportTicketAdmin(ModelAdmin):
    inlines = [TicketReplyInline]
    list_display = ['ticket_number', 'user', 'subject', 'status_badge', 'priority_badge', 'created_at', 'quick_ticket_actions']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['ticket_number', 'subject']
    readonly_fields = ['ticket_number', 'created_at', 'updated_at']
    formfield_overrides = {
        db_models.DateTimeField: {'widget': DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M')},
    }
    actions = [export_to_csv, mark_ticket_resolved, mark_ticket_closed, send_reminder_email]
    
    fieldsets = [
        ('Ticket Information', {
            'fields': ['ticket_number', 'user', 'status', 'priority']
        }),
        ('Ticket Details', {
            'fields': ['subject', 'description']
        }),
        ('Resolution', {
            'fields': ['assigned_to', 'resolution', 'resolved_date']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at']
        }),
    ]
    
    def status_badge(self, obj):
        colors = {
            'open': '#FFA500',
            'in_progress': '#2196F3',
            'awaiting_response': '#9C27B0',
            'resolved': '#4CAF50',
            'closed': '#607D8B',
        }
        color = colors.get(obj.status, '#999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def priority_badge(self, obj):
        colors = {
            'low': '#4CAF50',
            'medium': '#FF9800',
            'high': '#F44336',
        }
        color = colors.get(obj.priority, '#999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('<int:pk>/resolve/', self.admin_site.admin_view(self.resolve_view), name='supportticket_resolve'),
            path('<int:pk>/close/',   self.admin_site.admin_view(self.close_view),   name='supportticket_close'),
        ]
        return custom + urls

    def resolve_view(self, request, pk):
        obj = SupportTicket.objects.get(pk=pk)
        obj.status = 'resolved'
        obj.save()
        messages.success(request, f'✅ Ticket {obj.ticket_number} resolved.')
        return HttpResponseRedirect(reverse('admin:myapp_supportticket_changelist'))

    def close_view(self, request, pk):
        obj = SupportTicket.objects.get(pk=pk)
        obj.status = 'closed'
        obj.save()
        messages.success(request, f'🔒 Ticket {obj.ticket_number} closed.')
        return HttpResponseRedirect(reverse('admin:myapp_supportticket_changelist'))

    def quick_ticket_actions(self, obj):
        if obj.status in ('resolved', 'closed'):
            return format_html('<span style="color:#999;font-size:0.78rem;">—</span>')
        resolve_url = reverse('admin:supportticket_resolve', args=[obj.pk])
        close_url   = reverse('admin:supportticket_close',   args=[obj.pk])
        return format_html(
            '<a href="{}" style="background:#3a9e25;color:#fff;padding:4px 10px;border-radius:6px;'
            'font-size:0.75rem;font-weight:700;text-decoration:none;margin-right:4px;"'
            ' onclick="return confirm(\'Mark ticket as resolved?\')">✅ Resolve</a>'
            '<a href="{}" style="background:#607D8B;color:#fff;padding:4px 10px;border-radius:6px;'
            'font-size:0.75rem;font-weight:700;text-decoration:none;"'
            ' onclick="return confirm(\'Close this ticket?\')">🔒 Close</a>',
            resolve_url, close_url
        )
    quick_ticket_actions.short_description = 'Quick Actions'
    quick_ticket_actions.allow_tags = True


# Group Admin
if admin.site.is_registered(Group):
    admin.site.unregister(Group)

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass

if admin.site.is_registered(TicketReply):
    admin.site.unregister(TicketReply)

@admin.register(TicketReply)
class TicketReplyAdmin(ModelAdmin):
    list_display = ['ticket', 'author', 'is_staff_reply', 'created_at']
    list_filter = ['is_staff_reply', 'created_at']
    search_fields = ['ticket__ticket_number', 'message']
    readonly_fields = ['created_at']
