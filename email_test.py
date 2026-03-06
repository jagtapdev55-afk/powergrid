import os
import django
import socket

# 1. Setup Django so we can use settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("\n--- DIAGNOSTIC START ---")
print(f"1. Email Backend: {settings.EMAIL_BACKEND}")
print(f"2. Email User: {settings.EMAIL_HOST_USER}")
print(f"3. Email Host: {settings.EMAIL_HOST}")
print(f"4. Port: {settings.EMAIL_PORT}")

try:
    print("5. Attempting to connect to Gmail...")
    send_mail(
        subject='Test Email',
        message='This is a test to see if credentials work.',
        from_email=None, 
        recipient_list=[settings.EMAIL_HOST_USER], # Sends to yourself
        fail_silently=False,
    )
    print("✅ SUCCESS! Email sent. Check your inbox.")
except socket.gaierror:
    print("❌ NETWORK ERROR: No internet connection or DNS failure.")
except Exception as e:
    print(f"❌ FAILURE: {e}")
    error_msg = str(e)
    print("\n--- SUGGESTED FIX ---")
    if "Application-specific password" in error_msg:
        print(">> You are using your normal Gmail password. You MUST use an App Password.")
    elif "Authentication required" in error_msg or "Username and Password not accepted" in error_msg:
        print(">> Your .env file might be wrong, or the password is incorrect.")
    elif "ConnectionRefused" in error_msg:
        print(">> Your firewall or antivirus is blocking the connection.")
print("--- DIAGNOSTIC END ---\n")