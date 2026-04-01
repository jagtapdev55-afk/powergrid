from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='user_profile'),  # NEW .profile_view
    path('change-password/', views.change_password_view, name='change_password'),
    
     # Consumer Numbers
    path('consumer-numbers/', views.consumer_numbers_view, name='consumer_numbers'),
    path('consumer-numbers/add/', views.add_consumer_number_view, name='add_consumer_number'),
    
    # Notifications
    path('notifications/', views.notifications_view, name='notifications_view'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # Email Preferences
    path('email-preferences/', views.email_preferences_view, name='email_preferences'),
    
    path('forgot-password/',         views.forgot_password_step1, name='forgot_password_step1'),
    path('forgot-password/verify/',  views.forgot_password_step2, name='forgot_password_step2'),
    path('forgot-password/reset/',   views.forgot_password_step3, name='forgot_password_step3'),
    path('forgot-password/resend/',  views.forgot_resend_otp,     name='forgot_resend_otp'),

# Also add this alias so the login template {% url 'accounts:password_reset' %} works:
    path('forgot-password/',         views.forgot_password_step1, name='password_reset'),
]