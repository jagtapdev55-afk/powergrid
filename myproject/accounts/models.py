
from django.conf import settings
from django.utils import timezone 
from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    DEPARTMENT_CHOICES = [
        ('admin', 'Administration'),
        ('technical', 'Technical Department'),
        ('billing', 'Billing Department'),
        ('customer_service', 'Customer Service'),
        ('maintenance', 'Maintenance'),
    ]
    
    # Basic Info
    phone = models.CharField(max_length=15, blank=True)
    employee_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Additional Info
    address = models.TextField(blank=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    date_of_joining = models.DateField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.username
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

#email otp 
class EmailOTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='email_otps', null=True, blank=True)
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Email OTP'
        verbose_name_plural = 'Email OTPs'
        ordering = ['-created_at']
    
    def is_valid(self):
        """Check if OTP is still valid (10 minutes)"""
        return timezone.now() < self.expires_at and not self.is_verified
    
    def __str__(self):
        return f"{self.email} - {self.otp_code}"

#login activity 
class LoginActivity(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='login_activities')
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255, blank=True)
    is_successful = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Login Activity'
        verbose_name_plural = 'Login Activities'
        ordering = ['-login_time']
    
    def __str__(self):
        return f"{self.user.username} - {self.login_time}"
#notification 
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=200, blank=True, help_text="Optional link to related page")
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_read']),
        ]
    
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    
    #Allow users to save multiple consumer numbers:
class ConsumerNumber(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='consumer_numbers')
    consumer_number = models.CharField(max_length=50, unique=True)
    nickname = models.CharField(max_length=100, blank=True, help_text="e.g., Home, Office")
    address = models.TextField(blank=True)
    is_primary = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_primary', '-created_at']
        verbose_name = 'Consumer Number'
        verbose_name_plural = 'Consumer Numbers'
        indexes = [
            models.Index(fields=['user', '-is_primary']),
            models.Index(fields=['consumer_number']),
        ]
    
    def save(self, *args, **kwargs):
        # If this is set as primary, unset others
        if self.is_primary:
            ConsumerNumber.objects.filter(user=self.user, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.consumer_number} - {self.nickname or self.user.username}"
    

#Let users choose which emails they want to receive
class EmailPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='email_preferences')
    
    # Email preferences
    receive_status_updates = models.BooleanField(default=True, help_text="Receive updates on application status")
    receive_promotional_emails = models.BooleanField(default=True, help_text="Receive promotional offers")
    receive_payment_reminders = models.BooleanField(default=True, help_text="Receive bill payment reminders")
    receive_outage_alerts = models.BooleanField(default=True, help_text="Receive power outage notifications")
    receive_newsletters = models.BooleanField(default=False, help_text="Receive monthly newsletters")
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Email Preference'
        verbose_name_plural = 'Email Preferences'
    
    def __str__(self):
        return f"{self.user.username} - Email Preferences"
    
    #indexes for models for faster qureies 
