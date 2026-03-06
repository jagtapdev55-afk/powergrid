"""
signals.py — fires on every status change, sends email + bell notification.
"""

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings


# ── helpers ────────────────────────────────────────────────────────────────

def _notify(user, title, message, notif_type='info', link='/my-applications/'):
    try:
        from accounts.models import Notification
        Notification.objects.create(
            user=user, title=title, message=message,
            notification_type=notif_type, link=link)
    except Exception as e:
        print(f'[signals] Notification error: {e}')


def _email(to, subject, body):
    try:
        send_mail(subject=subject, message=body,
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=[to] if isinstance(to, str) else to,
                  fail_silently=False)
        print(f'[signals] Email sent -> {to}')
    except Exception as e:
        print(f'[signals] Email error: {e}')


def _snap(instance, sender, field='status'):
    if instance.pk:
        try:
            instance._old_status = getattr(sender.objects.get(pk=instance.pk), field)
        except sender.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


# ── status label maps ──────────────────────────────────────────────────────

CONN = {
    'pending':         ('info',    'Pending Review'),
    'under_review':    ('info',    'Under Review'),
    'site_inspection': ('warning', 'Site Inspection Scheduled'),
    'approved':        ('success', 'Approved'),
    'rejected':        ('error',   'Rejected'),
    'completed':       ('success', 'Connection Completed'),
}
COMP = {
    'registered':   ('info',    'Registered'),
    'acknowledged': ('info',    'Acknowledged'),
    'in_progress':  ('warning', 'In Progress'),
    'resolved':     ('success', 'Resolved'),
    'closed':       ('info',    'Closed'),
    'reopened':     ('warning', 'Reopened'),
}
PAY = {
    'pending':    ('info',    'Pending'),
    'processing': ('warning', 'Processing'),
    'completed':  ('success', 'Payment Confirmed'),
    'failed':     ('error',   'Payment Failed'),
    'refunded':   ('info',    'Refunded'),
}
OUT = {
    'reported':      ('info',    'Reported'),
    'acknowledged':  ('info',    'Acknowledged'),
    'investigating': ('warning', 'Under Investigation'),
    'repairing':     ('warning', 'Repair In Progress'),
    'resolved':      ('success', 'Power Restored'),
}
MTR = {
    'submitted': ('info',    'Submitted'),
    'verified':  ('success', 'Verified'),
    'rejected':  ('error',   'Rejected'),
    'billed':    ('success', 'Billed'),
}
TKT = {
    'open':              ('info',    'Open'),
    'in_progress':       ('warning', 'In Progress'),
    'awaiting_response': ('warning', 'Awaiting Your Response'),
    'resolved':          ('success', 'Resolved'),
    'closed':            ('info',    'Closed'),
}


# ── pre-save: snapshot ─────────────────────────────────────────────────────

@receiver(pre_save, sender='myapp.ConnectionRequest')
def conn_pre(sender, instance, **kwargs):   _snap(instance, sender)

@receiver(pre_save, sender='myapp.Complaint')
def comp_pre(sender, instance, **kwargs):   _snap(instance, sender)

@receiver(pre_save, sender='myapp.BillPayment')
def pay_pre(sender, instance, **kwargs):    _snap(instance, sender, 'payment_status')

@receiver(pre_save, sender='myapp.PowerOutage')
def out_pre(sender, instance, **kwargs):    _snap(instance, sender)

@receiver(pre_save, sender='myapp.MeterReading')
def mtr_pre(sender, instance, **kwargs):    _snap(instance, sender)

@receiver(pre_save, sender='myapp.SupportTicket')
def tkt_pre(sender, instance, **kwargs):    _snap(instance, sender)


# ── 1. CONNECTION REQUEST ──────────────────────────────────────────────────

@receiver(post_save, sender='myapp.ConnectionRequest')
def conn_post(sender, instance, created, **kwargs):
    user = instance.user
    old  = getattr(instance, '_old_status', None)
    new  = instance.status

    if created:
        _notify(user,
            title=f'Connection Request Received — {instance.request_number}',
            message='Your connection request is pending review. We will update you shortly.')
        _email(user.email,
            subject=f'PowerGrid — Connection Request {instance.request_number} Received',
            body=f"""Dear {instance.full_name},

Your connection request has been received.

Reference No : {instance.request_number}
Type         : {instance.get_connection_type_display()}
Status       : Pending Review

We will review your application within 3-5 business days.

Best regards,
PowerGrid Team""")
        return

    if old is not None and old != new:
        nt, label = CONN.get(new, ('info', new.replace('_', ' ').title()))
        extras = []
        if instance.admin_remarks:
            extras.append(f'Remarks          : {instance.admin_remarks}')
        if new == 'rejected' and instance.rejection_reason:
            extras.append(f'Rejection Reason : {instance.rejection_reason}')
        if new == 'site_inspection' and instance.inspection_date:
            extras.append(f'Inspection Date  : {instance.inspection_date.strftime("%d %b %Y, %I:%M %p")}')
        ext = '\n'.join(extras)

        _notify(user, notif_type=nt,
            title=f'Connection Request Update — {instance.request_number}',
            message=f'Status updated to "{label}". {instance.admin_remarks[:80] if instance.admin_remarks else ""}')
        _email(instance.email,
            subject=f'PowerGrid — Connection Request {instance.request_number}: {label}',
            body=f"""Dear {instance.full_name},

Your connection request status has been updated.

Reference No    : {instance.request_number}
Previous Status : {old.replace('_', ' ').title()}
New Status      : {label}
{ext}

Track your application: http://127.0.0.1:8000/my-applications/

Best regards,
PowerGrid Team""")


# ── 2. COMPLAINT ───────────────────────────────────────────────────────────

@receiver(post_save, sender='myapp.Complaint')
def comp_post(sender, instance, created, **kwargs):
    user = instance.user
    old  = getattr(instance, '_old_status', None)
    new  = instance.status

    if created:
        _notify(user,
            title=f'Complaint Registered — {instance.complaint_number}',
            message=f'Your complaint "{instance.subject}" has been registered.')
        _email(instance.email,
            subject=f'PowerGrid — Complaint {instance.complaint_number} Registered',
            body=f"""Dear {instance.full_name},

Your complaint has been registered.

Complaint No : {instance.complaint_number}
Category     : {instance.get_category_display()}
Subject      : {instance.subject}
Status       : Registered

Our team will respond within 24-48 hours.

Best regards,
PowerGrid Support Team""")
        return

    if old is not None and old != new:
        nt, label = COMP.get(new, ('info', new.replace('_', ' ').title()))
        ext = f'Resolution : {instance.resolution_details}' if instance.resolution_details else ''

        _notify(user, notif_type=nt,
            title=f'Complaint Update — {instance.complaint_number}',
            message=f'Status changed to "{label}". {instance.resolution_details[:80] if instance.resolution_details else ""}')
        _email(instance.email,
            subject=f'PowerGrid — Complaint {instance.complaint_number}: {label}',
            body=f"""Dear {instance.full_name},

Your complaint status has been updated.

Complaint No    : {instance.complaint_number}
Subject         : {instance.subject}
Previous Status : {old.replace('_', ' ').title()}
New Status      : {label}
{ext}

Track: http://127.0.0.1:8000/my-applications/

Best regards,
PowerGrid Support Team""")


# ── 3. BILL PAYMENT ────────────────────────────────────────────────────────

@receiver(post_save, sender='myapp.BillPayment')
def pay_post(sender, instance, created, **kwargs):
    user = instance.user
    old  = getattr(instance, '_old_status', None)
    new  = instance.payment_status

    if created:
        _notify(user,
            title=f'Payment Initiated — {instance.payment_id}',
            message=f'Payment of Rs {instance.paid_amount} for consumer {instance.consumer_number} is processing.')
        _email(user.email,
            subject=f'PowerGrid — Payment {instance.payment_id} Initiated',
            body=f"""Dear Customer,

Your bill payment has been initiated.

Payment ID      : {instance.payment_id}
Consumer Number : {instance.consumer_number}
Billing Month   : {instance.billing_month}
Amount          : Rs {instance.paid_amount}
Method          : {instance.get_payment_method_display()}
Status          : Pending

You will be notified once payment is confirmed.

Best regards,
PowerGrid Billing Team""")
        return

    if old is not None and old != new:
        nt, label = PAY.get(new, ('info', new.replace('_', ' ').title()))
        extras = []
        if instance.transaction_id:
            extras.append(f'Transaction ID : {instance.transaction_id}')
        if instance.payment_date:
            extras.append(f'Payment Date   : {instance.payment_date.strftime("%d %b %Y, %I:%M %p")}')
        if instance.remarks:
            extras.append(f'Remarks        : {instance.remarks}')
        ext = '\n'.join(extras)

        _notify(user, notif_type=nt,
            title=f'Payment {label} — {instance.payment_id}',
            message=f'Rs {instance.paid_amount} for consumer {instance.consumer_number}: {label}.')
        _email(user.email,
            subject=f'PowerGrid — Payment {instance.payment_id}: {label}',
            body=f"""Dear Customer,

Your bill payment status has been updated.

Payment ID      : {instance.payment_id}
Consumer Number : {instance.consumer_number}
Billing Month   : {instance.billing_month}
Amount          : Rs {instance.paid_amount}
Previous Status : {old.replace('_', ' ').title()}
New Status      : {label}
{ext}

Best regards,
PowerGrid Billing Team""")


# ── 4. POWER OUTAGE ────────────────────────────────────────────────────────

@receiver(post_save, sender='myapp.PowerOutage')
def out_post(sender, instance, created, **kwargs):
    user = instance.user
    old  = getattr(instance, '_old_status', None)
    new  = instance.status

    if created:
        _notify(user, notif_type='warning',
            title=f'Outage Report Received — {instance.report_number}',
            message=f'Outage reported for "{instance.area}". Technical team notified.')
        _email(user.email,
            subject=f'PowerGrid — Outage Report {instance.report_number} Received',
            body=f"""Dear {instance.full_name},

Your power outage report has been received.

Report No   : {instance.report_number}
Area        : {instance.area}
Outage Type : {instance.get_outage_type_display()}
Status      : Reported

Our technical team has been notified.

Best regards,
PowerGrid Technical Team""")
        return

    if old is not None and old != new:
        nt, label = OUT.get(new, ('info', new.replace('_', ' ').title()))
        extras = []
        if instance.cause:
            extras.append(f'Cause                : {instance.cause}')
        if instance.estimated_resolution_time:
            extras.append(f'Estimated Resolution : {instance.estimated_resolution_time.strftime("%d %b %Y, %I:%M %p")}')
        if instance.resolution_details:
            extras.append(f'Details              : {instance.resolution_details}')
        ext = '\n'.join(extras)

        _notify(user, notif_type=nt,
            title=f'Outage Update — {instance.report_number}',
            message=f'Area "{instance.area}": {label}.')
        _email(user.email,
            subject=f'PowerGrid — Outage {instance.report_number}: {label}',
            body=f"""Dear {instance.full_name},

Your outage report status has been updated.

Report No       : {instance.report_number}
Area            : {instance.area}
Previous Status : {old.replace('_', ' ').title()}
New Status      : {label}
{ext}

Best regards,
PowerGrid Technical Team""")


# ── 5. METER READING ───────────────────────────────────────────────────────

@receiver(post_save, sender='myapp.MeterReading')
def mtr_post(sender, instance, created, **kwargs):
    user = instance.user
    old  = getattr(instance, '_old_status', None)
    new  = instance.status

    if created:
        _notify(user,
            title=f'Meter Reading Submitted — {instance.reading_id}',
            message=f'{instance.units_consumed} units for consumer {instance.consumer_number}. Pending verification.')
        _email(user.email,
            subject=f'PowerGrid — Meter Reading {instance.reading_id} Submitted',
            body=f"""Dear Customer,

Your meter reading has been submitted.

Reading ID      : {instance.reading_id}
Consumer Number : {instance.consumer_number}
Reading Date    : {instance.reading_date}
Current Reading : {instance.current_reading}
Previous Reading: {instance.previous_reading}
Units Consumed  : {instance.units_consumed}
Status          : Pending Verification

Best regards,
PowerGrid Billing Team""")
        return

    if old is not None and old != new:
        nt, label = MTR.get(new, ('info', new.replace('_', ' ').title()))
        ext = f'Remarks : {instance.admin_remarks}' if instance.admin_remarks else ''

        _notify(user, notif_type=nt,
            title=f'Meter Reading {label} — {instance.reading_id}',
            message=f'Consumer {instance.consumer_number}: {label}. {instance.admin_remarks[:60] if instance.admin_remarks else ""}')
        _email(user.email,
            subject=f'PowerGrid — Meter Reading {instance.reading_id}: {label}',
            body=f"""Dear Customer,

Your meter reading status has been updated.

Reading ID      : {instance.reading_id}
Consumer Number : {instance.consumer_number}
Units Consumed  : {instance.units_consumed}
Previous Status : {old.replace('_', ' ').title()}
New Status      : {label}
{ext}

Best regards,
PowerGrid Billing Team""")


# ── 6. SUPPORT TICKET ──────────────────────────────────────────────────────

@receiver(post_save, sender='myapp.SupportTicket')
def tkt_post(sender, instance, created, **kwargs):
    user = instance.user
    old  = getattr(instance, '_old_status', None)
    new  = instance.status
    link = f'/services/support/ticket/{instance.pk}/'

    if created:
        _notify(user, link=link,
            title=f'Support Ticket Created — {instance.ticket_number}',
            message=f'Ticket "{instance.subject}" received. We will respond shortly.')
        _email(user.email,
            subject=f'PowerGrid — Support Ticket {instance.ticket_number} Created',
            body=f"""Dear {user.get_full_name() or user.username},

Your support ticket has been created.

Ticket No : {instance.ticket_number}
Subject   : {instance.subject}
Priority  : {instance.get_priority_display()}
Status    : Open

View ticket: http://127.0.0.1:8000{link}

Best regards,
PowerGrid Support Team""")
        return

    if old is not None and old != new:
        nt, label = TKT.get(new, ('info', new.replace('_', ' ').title()))
        ext = f'Resolution : {instance.resolution}' if instance.resolution else ''

        _notify(user, notif_type=nt, link=link,
            title=f'Ticket Update — {instance.ticket_number}',
            message=f'"{instance.subject}" is now: {label}.')
        _email(user.email,
            subject=f'PowerGrid — Ticket {instance.ticket_number}: {label}',
            body=f"""Dear {user.get_full_name() or user.username},

Your support ticket has been updated.

Ticket No       : {instance.ticket_number}
Subject         : {instance.subject}
Previous Status : {old.replace('_', ' ').title()}
New Status      : {label}
{ext}

View ticket: http://127.0.0.1:8000{link}

Best regards,
PowerGrid Support Team""")


# ── 7. TICKET REPLY ────────────────────────────────────────────────────────

@receiver(post_save, sender='myapp.TicketReply')
def reply_post(sender, instance, created, **kwargs):
    if not created or not instance.is_staff_reply:
        return

    ticket = instance.ticket
    user   = ticket.user
    link   = f'/services/support/ticket/{ticket.pk}/'

    _notify(user, notif_type='info', link=link,
        title=f'Staff replied on Ticket {ticket.ticket_number}',
        message=f'"{instance.message[:100]}"')
    _email(user.email,
        subject=f'PowerGrid — New reply on Ticket {ticket.ticket_number}',
        body=f"""Dear {user.get_full_name() or user.username},

PowerGrid staff replied to your support ticket.

Ticket  : {ticket.ticket_number}
Subject : {ticket.subject}

Reply:
{instance.message}

View conversation: http://127.0.0.1:8000{link}

Best regards,
PowerGrid Support Team""")
