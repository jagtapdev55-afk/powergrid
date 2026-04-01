from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .models import CustomUser, EmailOTP, LoginActivity, Notification
from .forms import RegisterForm, LoginForm
from myapp.utils import send_email
import random
import threading
import urllib.request
import urllib.parse
import json
from django.utils import timezone
from django.core.mail import send_mail
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect, get_object_or_404

from .models import CustomUser, ConsumerNumber, EmailPreference\

import string
from django.shortcuts import render, redirect

from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage




def send_email_async(subject, message, recipient_list):
    """
    Fire-and-forget email — runs in background thread.
    Login/dashboard load is NOT blocked waiting for SMTP.
    """
    def _send():
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=recipient_list,
                fail_silently=True,   # never crash the thread
            )
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()






def generate_otp():
    """Generate 6-digit OTP"""
    return str(random.randint(100000, 999999))


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def register_view(request):
    if request.user.is_authenticated:
        return redirect('admin:index')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        
        if form.is_valid():
            # Create user
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_verified = False
            
            address = form.cleaned_data.get('address', '')
           
            user.save()
            
            # Generate OTP
            otp_code = generate_otp()
            expires_at = timezone.now() + timedelta(minutes=10)
            
            EmailOTP.objects.create(
                user=user,
                email=user.email,
                otp_code=otp_code,
                expires_at=expires_at,
                ip_address=get_client_ip(request)
            )
            
            # --- START EMAIL SENDING BLOCK ---
            try:
                print(f"Attempting to send email to: {user.email}") # Debug Print
                send_mail(
                    subject='Welcome to Electricity Company - Verify Your Email',
                    message=f'''
Dear {user.first_name or user.username},

Welcome to Electricity Company Admin Portal!

Your Email Verification Code: {otp_code}

This code will expire in 10 minutes.
                    ''',
                    from_email=None,  # This uses DEFAULT_FROM_EMAIL from settings
                    recipient_list=[user.email],  # <--- CRITICAL: MUST BE A LIST
                    fail_silently=False,
                )
                print("✅ Email sent successfully!") # Debug Print
                messages.success(request, '✅ Registration successful! Please check your email for OTP.')
                
            except Exception as e:
                print(f"❌ CRITICAL EMAIL ERROR: {e}") # Debug Print
                messages.warning(request, f'⚠️ Account created, but email failed: {e}')
            # --- END EMAIL SENDING BLOCK ---

            # Store session data
            request.session['verify_user_id'] = user.id
            request.session['verify_email'] = user.email
            
            return redirect('accounts:verify_otp')
    else:
        form = RegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def verify_otp_view(request):
    if 'verify_user_id' not in request.session:
        messages.error(request, '❌ Invalid session. Please register again.')
        return redirect('accounts:register')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        user_id = request.session.get('verify_user_id')
        
        try:
            user = CustomUser.objects.get(id=user_id)
            otp = EmailOTP.objects.filter(
                user=user,
                otp_code=otp_code,
                is_verified=False
            ).first()
            
            if otp and otp.is_valid():
                # Mark OTP as verified
                otp.is_verified = True
                otp.save()
                
                # Mark user as verified
                user.is_verified = True
                user.email_verified_at = timezone.now()
                user.save()
                
                # Send welcome email
                send_email(
                    recipient_list=[user.email] ,
                    subject='Email Verified Successfully - Welcome!',
                    message=f'''
Dear {user.get_full_name() or user.username},

Congratulations! Your email has been successfully verified.

Your account is now active and ready to use.

Account Details:
- Username: {user.username}
- Email: {user.email}
- Verified on: {timezone.now().strftime("%d %B %Y, %I:%M %p")}

You can now login to access the Electricity Company Admin Portal.

Login URL: http://127.0.0.1:8000/accounts/login/

If you have any questions, feel free to contact our support team.

Best regards,
Electricity Company Admin Team
                    '''
                )
                
                # Clear session
                del request.session['verify_user_id']
                del request.session['verify_email']
                
                # Log the user in
                login(request, user)
                
                # Log login activity
                LoginActivity.objects.create(
                    user=user,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                    is_successful=True
                )
                
                messages.success(request, f'✅ Email verified successfully! Welcome, {user.get_full_name() or user.username}!')
                if user.is_staff or user.is_superuser:
                    return redirect('admin:index')
                else:
                     return redirect('user_dashboard')
            else:
                messages.error(request, '❌ Invalid or expired OTP. Please try again.')
        
        except CustomUser.DoesNotExist:
            messages.error(request, '❌ User not found.')
            return redirect('accounts:register')
        
    
    return render(request, 'accounts/verify_otp.html', {
        'email': request.session.get('verify_email')
    })
    
    if user.is_staff or user.is_superuser:
          return redirect('admin:index')
    else:
          return redirect('user_dashboard') 
    
      


def resend_otp_view(request):
    if 'verify_user_id' not in request.session:
        messages.error(request, '❌ Invalid session.')
        return redirect('accounts:register')
    
    user_id = request.session.get('verify_user_id')
    user = CustomUser.objects.get(id=user_id)
    
    # Generate new OTP
    otp_code = generate_otp()
    expires_at = timezone.now() + timedelta(minutes=10)
    
    EmailOTP.objects.create(
        user=user,
        email=user.email,
        otp_code=otp_code,
        expires_at=expires_at,
        ip_address=get_client_ip(request)
    )
    
    # Send new OTP email
    send_email(
        recipient_list=[user.email] ,
        subject='Email Verification - New OTP Code',
        message=f'''
Dear {user.get_full_name() or user.username},

You requested a new verification code.

Your New Verification Code: {otp_code}

This code will expire in 10 minutes.

If you didn't request this, please ignore this email.

Best regards,
Electricity Company Admin Team
        '''
    )
    
    messages.success(request, '✅ New OTP sent to your email!')
    return redirect('accounts:verify_otp')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('admin:index')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_verified:
                    login(request, user)
                    
                    # Send in background thread — does NOT block the redirect
                    import threading
                    def _send_login_email():
                        try:
                            send_email(
                                recipient_list=[user.email],
                                subject='New Login to Your Account',
                                message=f'''
Dear {user.get_full_name() or user.username},

A new login was detected on your account.

Login Details:
- Date & Time: {timezone.now().strftime("%d %B %Y, %I:%M %p")}
- IP Address: {get_client_ip(request)}
- Device: {request.META.get('HTTP_USER_AGENT', 'Unknown')[:100]}

If this wasn't you, please change your password immediately and contact support.

Best regards,
Electricity Company Admin Team
                        '''
                            )
                        except Exception:
                            pass
                    threading.Thread(target=_send_login_email, daemon=True).start()
                    
                    # Log login activity
                    LoginActivity.objects.create(
                        user=user,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                        is_successful=True
                    )
                    
                    next_page = request.GET.get('next')
                    if next_page:
                        return redirect(next_page)
                    elif user.is_staff or user.is_superuser:
                        return redirect('admin:index')
                    else:
                        return redirect('user_dashboard')
                else:
                    messages.error(request, '❌ Please verify your email first.')
            else:
                # Log failed login attempt
                try:
                    failed_user = CustomUser.objects.get(username=username)
                    LoginActivity.objects.create(
                        user=failed_user,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                        is_successful=False
                    )
                except CustomUser.DoesNotExist:
                    pass
                
                messages.error(request, '❌ Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})
    
    if user.is_staff or user.is_superuser:
      return redirect('admin:index')
    else:
      return redirect('user_dashboard') 
  
  
@login_required
def profile_view(request):
    """User profile and settings"""
    if request.method == 'POST':
        user = request.user
        
        # Update basic info
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.phone = request.POST.get('phone', '')
        user.address = request.POST.get('address', '')
        user.save()
        
        messages.success(request, '✅ Profile updated successfully!')
        return redirect('accounts:user_profile')
    
    # Get user's recent activities
    recent_logins = LoginActivity.objects.filter(user=request.user)[:10]
    
    context = {
        'user': request.user,
        'recent_logins': recent_logins,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def change_password_view(request):
    """Change password"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        user = request.user
        
        # Verify old password
        if not user.check_password(old_password):
            messages.error(request, '❌ Current password is incorrect.')
            return redirect('accounts:change_password')
        
        # Check if new passwords match
        if new_password != confirm_password:
            messages.error(request, '❌ New passwords do not match.')
            return redirect('accounts:change_password')
        
        # Update password
        user.set_password(new_password)
        user.save()
        
        # Send email notification
        send_email(
            subject='Password Changed Successfully',
            message=f'''
Dear {user.get_full_name() or user.username},

Your password has been changed successfully.

If you did not make this change, please contact support immediately.

Best regards,
PowerGrid Team
            ''',
            recipient_list=[user.email]
        )
        
        messages.success(request, '✅ Password changed successfully! Please login again.')
        return redirect('accounts:login')
    
    return render(request, 'accounts/change_password.html')

      


def logout_view(request):
    if request.user.is_authenticated:
        last_activity = LoginActivity.objects.filter(
            user=request.user,
            logout_time__isnull=True
        ).first()
        if last_activity:
            last_activity.logout_time = timezone.now()
            last_activity.save()
        user_id = request.user.id
        username = request.user.username
        logout(request)
        messages.success(request, f'✅ Goodbye, {username}! You have been logged out successfully.')
        response = redirect('accounts:login')
        response.delete_cookie(f'pgv5uid{user_id}')
        return response
    return redirect('accounts:login')
        
        


@login_required
def consumer_numbers_view(request):
    """Manage consumer numbers"""
    consumer_numbers = ConsumerNumber.objects.filter(user=request.user)
    
    context = {
        'consumer_numbers': consumer_numbers,
    }
    return render(request, 'accounts/consumer_numbers.html', context)


@login_required
def add_consumer_number_view(request):
    """Add new consumer number"""
    if request.method == 'POST':
        consumer_number = request.POST.get('consumer_number')
        nickname = request.POST.get('nickname')
        address = request.POST.get('address')
        is_primary = request.POST.get('is_primary') == 'on'
        
        # Check if consumer number already exists
        if ConsumerNumber.objects.filter(consumer_number=consumer_number).exists():
            messages.error(request, '❌ This consumer number is already registered.')
            return redirect('accounts:consumer_numbers')
        
        # Create consumer number
        ConsumerNumber.objects.create(
            user=request.user,
            consumer_number=consumer_number,
            nickname=nickname,
            address=address,
            is_primary=is_primary
        )
        
        messages.success(request, '✅ Consumer number added successfully!')
        return redirect('accounts:consumer_numbers')
    
    return render(request, 'accounts/add_consumer_number.html')


@login_required
def notifications_view(request):
    """View all notifications"""
    notifications = Notification.objects.filter(user=request.user)
    unread_count = notifications.filter(is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'accounts/notifications.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    notification = Notification.objects.filter(id=notification_id, user=request.user).first()
    if notification:
        notification.mark_as_read()
    
    return redirect('accounts:notifications_view')


@login_required
def email_preferences_view(request):
    """Manage email preferences"""
    # Get or create email preferences
    preferences, created = EmailPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        preferences.receive_status_updates = request.POST.get('receive_status_updates') == 'on'
        preferences.receive_promotional_emails = request.POST.get('receive_promotional_emails') == 'on'
        preferences.receive_payment_reminders = request.POST.get('receive_payment_reminders') == 'on'
        preferences.receive_outage_alerts = request.POST.get('receive_outage_alerts') == 'on'
        preferences.receive_newsletters = request.POST.get('receive_newsletters') == 'on'
        preferences.save()
        
        messages.success(request, '✅ Email preferences updated successfully!')
        return redirect('accounts:email_preferences')
    
    context = {
        'preferences': preferences,
    }
    return render(request, 'accounts/email_preferences.html', context)

User = get_user_model()


def generate_otp():
    """Generate a 6-digit numeric OTP."""
    return ''.join(random.choices(string.digits, k=6))


# ══════════════════════════════════════════════════════════════════
# STEP 1 — Enter Username
# ══════════════════════════════════════════════════════════════════

def forgot_password_step1(request):
    """
    User enters their username.
    System finds the email attached to that username and sends OTP.
    """
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()

        if not username:
            messages.error(request, 'Please enter your username.')
            return render(request, 'accounts/forgot_step1.html')

        # Find user by username
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Don't reveal if username exists — security
            messages.error(request, 'No account found with that username.')
            return render(request, 'accounts/forgot_step1.html')

        if not user.email:
            messages.error(request, 'No email address is linked to this account. Please contact support.')
            return render(request, 'accounts/forgot_step1.html')

        # Generate OTP
        otp_code = generate_otp()
        expires_at = timezone.now() + timedelta(minutes=10)

        # Save OTP using your existing EmailOTP model
        from accounts.models import EmailOTP
        # Delete any old unused OTPs for this email
        EmailOTP.objects.filter(email=user.email, is_verified=False).delete()

        EmailOTP.objects.create(
            email      = user.email,
            otp_code   = otp_code,
            is_verified= False,
            expires_at = expires_at,
        )

        # Send OTP email
        masked_email = mask_email(user.email)
        try:
            send_otp_email(user.email, otp_code, user.username)
            # Store username in session to use in next steps
            request.session['reset_username'] = username
            request.session['reset_email']    = user.email
            messages.success(request, f'OTP sent to {masked_email}')
            return redirect('accounts:forgot_password_step2')
        except Exception as e:
            messages.error(request, 'Failed to send OTP. Please try again.')
            return render(request, 'accounts/forgot_step1.html')

    return render(request, 'accounts/forgot_step1.html')


# ══════════════════════════════════════════════════════════════════
# STEP 2 — Enter OTP
# ══════════════════════════════════════════════════════════════════

def forgot_password_step2(request):
    """
    User enters the 6-digit OTP received on email.
    """
    # Must have gone through step 1
    if 'reset_username' not in request.session:
        return redirect('accounts:forgot_password_step1')

    email    = request.session.get('reset_email', '')
    masked   = mask_email(email)

    if request.method == 'POST':
        otp_entered = request.POST.get('otp', '').strip()

        if not otp_entered:
            messages.error(request, 'Please enter the OTP.')
            return render(request, 'accounts/forgot_step2.html', {'masked_email': masked})

        from accounts.models import EmailOTP

        try:
            otp_obj = EmailOTP.objects.filter(
                email      = email,
                otp_code   = otp_entered,
                is_verified= False,
            ).latest('created_at')
        except EmailOTP.DoesNotExist:
            messages.error(request, 'Invalid OTP. Please check and try again.')
            return render(request, 'accounts/forgot_step2.html', {'masked_email': masked})

        # Check expiry
        if timezone.now() > otp_obj.expires_at:
            messages.error(request, 'OTP has expired. Please request a new one.')
            otp_obj.delete()
            return render(request, 'accounts/forgot_step2.html', {'masked_email': masked})

        # OTP is valid — mark as verified
        otp_obj.is_verified = True
        otp_obj.save()

        # Mark session as OTP verified — allow access to step 3
        request.session['reset_otp_verified'] = True

        messages.success(request, 'OTP verified! Now set your new password.')
        return redirect('accounts:forgot_password_step3')

    return render(request, 'accounts/forgot_step2.html', {'masked_email': masked})


# ══════════════════════════════════════════════════════════════════
# STEP 3 — Set New Password
# ══════════════════════════════════════════════════════════════════

def forgot_password_step3(request):
    """
    User sets their new password.
    Only accessible if OTP was verified in step 2.
    """
    # Must have completed step 2
    if not request.session.get('reset_otp_verified'):
        return redirect('accounts:forgot_password_step1')

    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not password1 or not password2:
            messages.error(request, 'Please fill in both fields.')
            return render(request, 'accounts/forgot_step3.html')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/forgot_step3.html')

        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'accounts/forgot_step3.html')

        # Get user from session
        username = request.session.get('reset_username')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'Session expired. Please start again.')
            return redirect('accounts:forgot_password_step1')

        # Set new password
        user.set_password(password1)
        user.save()

        # Clean up session
        for key in ['reset_username', 'reset_email', 'reset_otp_verified']:
            request.session.pop(key, None)

        # Clean up OTP records
        from accounts.models import EmailOTP
        EmailOTP.objects.filter(email=user.email).delete()

        messages.success(request, 'Password changed successfully! Please login with your new password.')
        return redirect('accounts:login')

    return render(request, 'accounts/forgot_step3.html')


# ══════════════════════════════════════════════════════════════════
# RESEND OTP
# ══════════════════════════════════════════════════════════════════

def forgot_resend_otp(request):
    """Resend OTP — called from step 2 page."""
    if 'reset_username' not in request.session:
        return redirect('accounts:forgot_password_step1')

    email    = request.session.get('reset_email', '')
    username = request.session.get('reset_username', '')

    otp_code  = generate_otp()
    expires_at = timezone.now() + timedelta(minutes=10)

    from accounts.models import EmailOTP
    EmailOTP.objects.filter(email=email, is_verified=False).delete()
    EmailOTP.objects.create(
        email      = email,
        otp_code   = otp_code,
        is_verified= False,
        expires_at = expires_at,
    )

    try:
        send_otp_email(email, otp_code, username)
        messages.success(request, f'New OTP sent to {mask_email(email)}')
    except Exception:
        messages.error(request, 'Failed to resend OTP.')

    return redirect('accounts:forgot_password_step2')


# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════

def mask_email(email):
    """
    Masks email for display: john@gmail.com → j***@gmail.com
    """
    if not email or '@' not in email:
        return email
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = local[0] + '***'
    else:
        masked_local = local[0] + '***' + local[-1]
    return f'{masked_local}@{domain}'


def send_otp_email(email, otp_code, username):
    """Send OTP email for password reset."""
    subject = 'PowerGrid — Password Reset OTP'
    body = f"""
Hello {username},

You requested a password reset for your PowerGrid account.

Your OTP is:

    {otp_code}

This OTP is valid for 10 minutes.

If you did not request this, please ignore this email.
Your password will remain unchanged.

— PowerGrid Security Team
"""
    msg = EmailMessage(
        subject   = subject,
        body      = body,
        to        = [email],
    )
    msg.send()