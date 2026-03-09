from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from accounts.models import Notification

def send_email(to_email, subject, message):
    """
    Simple function to send email
    
    Usage:
        send_email('user@example.com', 'Hello', 'This is a test message')
    
    Parameters:
        to_email (str): Recipient email address
        subject (str): Email subject
        message (str): Email body/message
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )
        print(f"✅ Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

def send_template_email(subject, template_name, context, recipient_list):
    """
    Send email using HTML template
    """
    html_content = render_to_string(template_name, context)
    return send_html_email(subject, html_content, recipient_list)

def send_simple_email(subject, message, recipient_list):
    """
    Send a simple text email
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_html_email(subject, html_content, recipient_list):
    """
    Send an HTML email
    """
    try:
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
        )
        email.content_subtype = 'html'  # Main content is text/html
        email.send()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_email_with_attachment(subject, message, recipient_list, file_path):
    """
    Send email with attachment
    """
    try:
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
        )
        email.attach_file(file_path)
        email.send()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_email(subject, message, recipient_list):
    """
    Generic send_email wrapper (uses simple text email)
    """
    return send_simple_email(subject, message, recipient_list)


def create_notification(user, title, message, notification_type='info', link=''):
    """Create a notification for a user"""
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link
    )


def notify_status_change(user, item_type, item_number, old_status, new_status):
    """Notify user when application status changes"""
    status_messages = {
        'approved': f'Your {item_type} {item_number} has been approved! ✓',
        'rejected': f'Your {item_type} {item_number} has been rejected.',
        'under_review': f'Your {item_type} {item_number} is now under review.',
        'completed': f'Your {item_type} {item_number} has been completed! ✓',
    }
    
    notification_types = {
        'approved': 'success',
        'completed': 'success',
        'rejected': 'error',
        'under_review': 'info',
    }
    
    message = status_messages.get(new_status, f'Your {item_type} {item_number} status has changed.')
    notification_type = notification_types.get(new_status, 'info')
    
    return create_notification(
        user=user,
        title=f'{item_type} Status Update',
        message=message,
        notification_type=notification_type,
        link='/my-applications/'
    )