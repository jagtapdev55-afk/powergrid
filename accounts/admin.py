from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import CustomUser, EmailOTP, LoginActivity, Notification, ConsumerNumber, EmailPreference


# ONLY REGISTER CustomUser ONCE
@admin.register(CustomUser)
class CustomUserAdmin(ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_verified', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_verified', 'department']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'employee_id']
    readonly_fields = ['date_joined', 'last_login', 'created_at']
    
    fieldsets = [
        ('Account Info', {
            'fields': ['username', 'password', 'email', 'is_verified', 'email_verified_at']
        }),
        ('Personal Info', {
            'fields': ['first_name', 'last_name', 'phone', 'address', 'employee_id', 'department', 'date_of_joining']
        }),
        ('Permissions', {
            'fields': ['is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions']
        }),
        ('Important Dates', {
            'fields': ['last_login', 'date_joined', 'created_at']
        }),
    ]


@admin.register(EmailOTP)
class EmailOTPAdmin(ModelAdmin):
    list_display = ['email', 'otp_code', 'is_verified', 'created_at', 'expires_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['email', 'otp_code']
    readonly_fields = ['created_at']


@admin.register(LoginActivity)
class LoginActivityAdmin(ModelAdmin):
    list_display = ['user', 'login_time', 'ip_address', 'is_successful']
    list_filter = ['is_successful', 'login_time']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['login_time', 'logout_time']


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at', 'read_at']
    
    fieldsets = [
        ('Notification Details', {
            'fields': ['user', 'title', 'message', 'notification_type', 'link']
        }),
        ('Status', {
            'fields': ['is_read', 'created_at', 'read_at']
        }),
    ]


@admin.register(ConsumerNumber)
class ConsumerNumberAdmin(ModelAdmin):
    list_display = ['consumer_number', 'user', 'nickname', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['consumer_number', 'user__username', 'nickname']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Consumer Info', {
            'fields': ['user', 'consumer_number', 'nickname', 'is_primary']
        }),
        ('Address', {
            'fields': ['address']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at']
        }),
    ]


@admin.register(EmailPreference)
class EmailPreferenceAdmin(ModelAdmin):
    list_display = ['user', 'receive_status_updates', 'receive_payment_reminders', 'receive_outage_alerts', 'updated_at']
    list_filter = ['receive_status_updates', 'receive_payment_reminders', 'receive_outage_alerts']
    search_fields = ['user__username']
    readonly_fields = ['updated_at']
    
    fieldsets = [
        ('User', {
            'fields': ['user']
        }),
        ('Email Preferences', {
            'fields': [
                'receive_status_updates',
                'receive_promotional_emails',
                'receive_payment_reminders',
                'receive_outage_alerts',
                'receive_newsletters'
            ]
        }),
        ('Last Updated', {
            'fields': ['updated_at']
        }),
    ]