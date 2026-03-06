"""
signals.py — fires on every status change.
Sends HTML email + bell notification to user.
"""

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone


# ── helpers ────────────────────────────────────────────────────────────────

def _notify(user, title, message, notif_type='info', link='/my-applications/'):
    try:
        from accounts.models import Notification
        Notification.objects.create(
            user=user, title=title, message=message,
            notification_type=notif_type, link=link)
    except Exception as e:
        print(f'[signals] Notification error: {e}')


def _html_email(to, subject, template, context):
    """Send a branded HTML email using a template."""
    try:
        html = render_to_string(template, context)
        msg  = EmailMessage(
            subject=subject,
            body=html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to] if isinstance(to, str) else to,
        )
        msg.content_subtype = 'html'
        msg.send()
        print(f'[signals] HTML email sent -> {to}')
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


# badge type map
def _badge(status):
    return {
        'approved': 'success', 'completed': 'success', 'resolved': 'success',
        'verified': 'success', 'billed': 'success',
        'rejected': 'error',   'failed': 'error',
        'in_progress': 'warning', 'repairing': 'warning', 'investigating': 'warning',
        'site_inspection': 'warning', 'reopened': 'warning', 'awaiting_response': 'warning',
        'processing': 'warning',
    }.get(status, 'info')


CONN_LABELS     = {'pending':('info','Pending Review'),'under_review':('info','Under Review'),'site_inspection':('warning','Site Inspection Scheduled'),'approved':('success','Approved'),'rejected':('error','Rejected'),'completed':('success','Connection Completed')}
COMPLAINT_LABELS= {'registered':('info','Registered'),'acknowledged':('info','Acknowledged'),'in_progress':('warning','In Progress'),'resolved':('success','Resolved'),'closed':('info','Closed'),'reopened':('warning','Reopened')}
PAYMENT_LABELS  = {'pending':('info','Pending'),'processing':('warning','Processing'),'completed':('success','Payment Confirmed'),'failed':('error','Payment Failed'),'refunded':('info','Refunded')}
OUTAGE_LABELS   = {'reported':('info','Reported'),'acknowledged':('info','Acknowledged'),'investigating':('warning','Under Investigation'),'repairing':('warning','Repair In Progress'),'resolved':('success','Power Restored')}
METER_LABELS    = {'submitted':('info','Submitted'),'verified':('success','Verified'),'rejected':('error','Rejected'),'billed':('success','Billed')}
TICKET_LABELS   = {'open':('info','Open'),'in_progress':('warning','In Progress'),'awaiting_response':('warning','Awaiting Your Response'),'resolved':('success','Resolved'),'closed':('info','Closed')}


# ── pre-save snapshots ─────────────────────────────────────────────────────
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
            message='Your connection request is pending review.')
        _html_email(instance.email,
            subject=f'PowerGrid — Connection Request {instance.request_number} Received',
            template='emails/status_update.html',
            context=dict(
                user_name=instance.full_name,
                item_type='Connection Request',
                reference_number=instance.request_number,
                subject=None,
                old_status='—',
                new_status='Pending Review',
                status_label='Pending Review',
                badge_type='info',
                extra_field_1_label='Connection Type',
                extra_field_1_value=instance.get_connection_type_display(),
                extra_field_2_label=None, extra_field_2_value=None,
                updated_at=instance.created_at.strftime('%d %b %Y, %I:%M %p'),
                remarks=None,
                track_url='http://127.0.0.1:8000/my-applications/',
            ))
        return

    if old is not None and old != new:
        nt, label = CONN_LABELS.get(new, ('info', new.replace('_',' ').title()))
        _notify(user, notif_type=nt,
            title=f'Connection Request Update — {instance.request_number}',
            message=f'Status updated to "{label}". {instance.admin_remarks[:80] if instance.admin_remarks else ""}')
        extras = []
        if new == 'site_inspection' and instance.inspection_date:
            extras = [('Inspection Date', instance.inspection_date.strftime('%d %b %Y, %I:%M %p')), (None, None)]
        elif new == 'rejected' and instance.rejection_reason:
            extras = [('Rejection Reason', instance.rejection_reason), (None, None)]
        else:
            extras = [(None, None), (None, None)]
        _html_email(instance.email,
            subject=f'PowerGrid — Connection Request {instance.request_number}: {label}',
            template='emails/status_update.html',
            context=dict(
                user_name=instance.full_name,
                item_type='Connection Request',
                reference_number=instance.request_number,
                subject=None,
                old_status=old.replace('_',' ').title(),
                new_status=label,
                status_label=label,
                badge_type=_badge(new),
                extra_field_1_label=extras[0][0], extra_field_1_value=extras[0][1],
                extra_field_2_label=extras[1][0], extra_field_2_value=extras[1][1],
                updated_at=timezone.now().strftime('%d %b %Y, %I:%M %p'),
                remarks=instance.admin_remarks or None,
                track_url='http://127.0.0.1:8000/my-applications/',
            ))


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
        _html_email(instance.email,
            subject=f'PowerGrid — Complaint {instance.complaint_number} Registered',
            template='emails/complaint_registered.html',
            context=dict(
                user_name=instance.full_name,
                complaint_number=instance.complaint_number,
                category=instance.get_category_display(),
                subject=instance.subject,
                priority=instance.get_priority_display(),
                submitted_at=instance.created_at.strftime('%d %b %Y, %I:%M %p'),
                track_url='http://127.0.0.1:8000/my-applications/',
            ))
        return

    if old is not None and old != new:
        nt, label = COMPLAINT_LABELS.get(new, ('info', new.replace('_',' ').title()))
        _notify(user, notif_type=nt,
            title=f'Complaint Update — {instance.complaint_number}',
            message=f'Status changed to "{label}". {instance.resolution_details[:80] if instance.resolution_details else ""}')
        _html_email(instance.email,
            subject=f'PowerGrid — Complaint {instance.complaint_number}: {label}',
            template='emails/status_update.html',
            context=dict(
                user_name=instance.full_name,
                item_type='Complaint',
                reference_number=instance.complaint_number,
                subject=instance.subject,
                old_status=old.replace('_',' ').title(),
                new_status=label,
                status_label=label,
                badge_type=_badge(new),
                extra_field_1_label='Category',
                extra_field_1_value=instance.get_category_display(),
                extra_field_2_label='Resolution' if instance.resolution_details else None,
                extra_field_2_value=instance.resolution_details or None,
                updated_at=timezone.now().strftime('%d %b %Y, %I:%M %p'),
                remarks=None,
                track_url='http://127.0.0.1:8000/my-applications/',
            ))


# ── 3. BILL PAYMENT ────────────────────────────────────────────────────────
@receiver(post_save, sender='myapp.BillPayment')
def pay_post(sender, instance, created, **kwargs):
    user = instance.user
    old  = getattr(instance, '_old_status', None)
    new  = instance.payment_status

    if created:
        _notify(user,
            title=f'Payment Initiated — {instance.payment_id}',
            message=f'Rs {instance.paid_amount} for consumer {instance.consumer_number} is processing.')
        _html_email(user.email,
            subject=f'PowerGrid — Payment {instance.payment_id} Initiated',
            template='emails/payment_email.html',
            context=dict(
                user_name=user.get_full_name() or user.username,
                is_confirmed=False,
                action='Initiated',
                amount=instance.paid_amount,
                payment_id=instance.payment_id,
                consumer_number=instance.consumer_number,
                billing_month=instance.billing_month,
                payment_method=instance.get_payment_method_display(),
                status_label='Pending',
                badge_type='info',
                transaction_id=None,
                payment_date=None,
                receipt_url=None,
            ))
        return

    if old is not None and old != new:
        nt, label = PAYMENT_LABELS.get(new, ('info', new.replace('_',' ').title()))
        _notify(user, notif_type=nt,
            title=f'Payment {label} — {instance.payment_id}',
            message=f'Rs {instance.paid_amount} for consumer {instance.consumer_number}: {label}.')
        _html_email(user.email,
            subject=f'PowerGrid — Payment {instance.payment_id}: {label}',
            template='emails/payment_email.html',
            context=dict(
                user_name=user.get_full_name() or user.username,
                is_confirmed=(new == 'completed'),
                action='Paid' if new == 'completed' else 'Updated',
                amount=instance.paid_amount,
                payment_id=instance.payment_id,
                consumer_number=instance.consumer_number,
                billing_month=instance.billing_month,
                payment_method=instance.get_payment_method_display(),
                status_label=label,
                badge_type=_badge(new),
                transaction_id=instance.transaction_id or None,
                payment_date=instance.payment_date.strftime('%d %b %Y, %I:%M %p') if instance.payment_date else None,
                receipt_url=f'http://127.0.0.1:8000/payments/{instance.payment_id}/receipt/',
            ))


# ── 4. POWER OUTAGE ────────────────────────────────────────────────────────
@receiver(post_save, sender='myapp.PowerOutage')
def out_post(sender, instance, created, **kwargs):
    user = instance.user
    old  = getattr(instance, '_old_status', None)
    new  = instance.status

    if created:
        _notify(user, notif_type='warning',
            title=f'Outage Report Received — {instance.report_number}',
            message=f'Outage reported for "{instance.area}".')
        _html_email(user.email,
            subject=f'PowerGrid — Outage Report {instance.report_number} Received',
            template='emails/status_update.html',
            context=dict(
                user_name=instance.full_name,
                item_type='Power Outage Report',
                reference_number=instance.report_number,
                subject=None,
                old_status='—',
                new_status='Reported',
                status_label='Reported',
                badge_type='warning',
                extra_field_1_label='Area', extra_field_1_value=instance.area,
                extra_field_2_label='Outage Type', extra_field_2_value=instance.get_outage_type_display(),
                updated_at=instance.created_at.strftime('%d %b %Y, %I:%M %p'),
                remarks=None,
                track_url='http://127.0.0.1:8000/my-applications/',
            ))
        return

    if old is not None and old != new:
        nt, label = OUTAGE_LABELS.get(new, ('info', new.replace('_',' ').title()))
        _notify(user, notif_type=nt,
            title=f'Outage Update — {instance.report_number}',
            message=f'Area "{instance.area}": {label}.')
        _html_email(user.email,
            subject=f'PowerGrid — Outage {instance.report_number}: {label}',
            template='emails/status_update.html',
            context=dict(
                user_name=instance.full_name,
                item_type='Power Outage Report',
                reference_number=instance.report_number,
                subject=None,
                old_status=old.replace('_',' ').title(),
                new_status=label,
                status_label=label,
                badge_type=_badge(new),
                extra_field_1_label='Area', extra_field_1_value=instance.area,
                extra_field_2_label='Estimated Resolution' if instance.estimated_resolution_time else None,
                extra_field_2_value=instance.estimated_resolution_time.strftime('%d %b %Y, %I:%M %p') if instance.estimated_resolution_time else None,
                updated_at=timezone.now().strftime('%d %b %Y, %I:%M %p'),
                remarks=instance.resolution_details or None,
                track_url='http://127.0.0.1:8000/my-applications/',
            ))


# ── 5. METER READING ───────────────────────────────────────────────────────
@receiver(post_save, sender='myapp.MeterReading')
def mtr_post(sender, instance, created, **kwargs):
    user = instance.user
    old  = getattr(instance, '_old_status', None)
    new  = instance.status

    if created:
        _notify(user,
            title=f'Meter Reading Submitted — {instance.reading_id}',
            message=f'{instance.units_consumed} units for consumer {instance.consumer_number}.')
        _html_email(user.email,
            subject=f'PowerGrid — Meter Reading {instance.reading_id} Submitted',
            template='emails/status_update.html',
            context=dict(
                user_name=user.get_full_name() or user.username,
                item_type='Meter Reading',
                reference_number=instance.reading_id,
                subject=None,
                old_status='—',
                new_status='Pending Verification',
                status_label='Submitted',
                badge_type='info',
                extra_field_1_label='Consumer Number', extra_field_1_value=instance.consumer_number,
                extra_field_2_label='Units Consumed', extra_field_2_value=instance.units_consumed,
                updated_at=instance.created_at.strftime('%d %b %Y, %I:%M %p'),
                remarks=None,
                track_url='http://127.0.0.1:8000/my-applications/',
            ))
        return

    if old is not None and old != new:
        nt, label = METER_LABELS.get(new, ('info', new.replace('_',' ').title()))
        _notify(user, notif_type=nt,
            title=f'Meter Reading {label} — {instance.reading_id}',
            message=f'Consumer {instance.consumer_number}: {label}.')
        _html_email(user.email,
            subject=f'PowerGrid — Meter Reading {instance.reading_id}: {label}',
            template='emails/status_update.html',
            context=dict(
                user_name=user.get_full_name() or user.username,
                item_type='Meter Reading',
                reference_number=instance.reading_id,
                subject=None,
                old_status=old.replace('_',' ').title(),
                new_status=label,
                status_label=label,
                badge_type=_badge(new),
                extra_field_1_label='Consumer Number', extra_field_1_value=instance.consumer_number,
                extra_field_2_label='Units Consumed', extra_field_2_value=instance.units_consumed,
                updated_at=timezone.now().strftime('%d %b %Y, %I:%M %p'),
                remarks=instance.admin_remarks or None,
                track_url='http://127.0.0.1:8000/my-applications/',
            ))


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
            message=f'Ticket "{instance.subject}" received.')
        _html_email(user.email,
            subject=f'PowerGrid — Support Ticket {instance.ticket_number} Created',
            template='emails/status_update.html',
            context=dict(
                user_name=user.get_full_name() or user.username,
                item_type='Support Ticket',
                reference_number=instance.ticket_number,
                subject=instance.subject,
                old_status='—',
                new_status='Open',
                status_label='Open',
                badge_type='info',
                extra_field_1_label='Priority', extra_field_1_value=instance.get_priority_display(),
                extra_field_2_label=None, extra_field_2_value=None,
                updated_at=instance.created_at.strftime('%d %b %Y, %I:%M %p'),
                remarks=None,
                track_url=f'http://127.0.0.1:8000{link}',
            ))
        return

    if old is not None and old != new:
        nt, label = TICKET_LABELS.get(new, ('info', new.replace('_',' ').title()))
        _notify(user, notif_type=nt, link=link,
            title=f'Ticket Update — {instance.ticket_number}',
            message=f'"{instance.subject}" is now: {label}.')
        _html_email(user.email,
            subject=f'PowerGrid — Ticket {instance.ticket_number}: {label}',
            template='emails/status_update.html',
            context=dict(
                user_name=user.get_full_name() or user.username,
                item_type='Support Ticket',
                reference_number=instance.ticket_number,
                subject=instance.subject,
                old_status=old.replace('_',' ').title(),
                new_status=label,
                status_label=label,
                badge_type=_badge(new),
                extra_field_1_label='Priority', extra_field_1_value=instance.get_priority_display(),
                extra_field_2_label='Resolution' if instance.resolution else None,
                extra_field_2_value=instance.resolution or None,
                updated_at=timezone.now().strftime('%d %b %Y, %I:%M %p'),
                remarks=None,
                track_url=f'http://127.0.0.1:8000{link}',
            ))


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
    _html_email(user.email,
        subject=f'PowerGrid — New reply on Ticket {ticket.ticket_number}',
        template='emails/ticket_reply.html',
        context=dict(
            user_name=user.get_full_name() or user.username,
            ticket_number=ticket.ticket_number,
            subject=ticket.subject,
            status=ticket.get_status_display(),
            reply_message=instance.message,
            ticket_url=f'http://127.0.0.1:8000{link}',
        ))


# ── 8. OUTAGE ANNOUNCEMENT (admin broadcasts to all users) ─────────────────
@receiver(post_save, sender='myapp.OutageAnnouncement')
def announcement_post(sender, instance, created, **kwargs):
    """When admin saves a new outage announcement with notify_users=True,
       send HTML email to every active user."""
    if not instance.notify_users:
        return
    if instance.notified_at:
        return  # already sent, don't send again on subsequent saves

    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Calculate duration
    delta = instance.end_datetime - instance.start_datetime
    hours = int(delta.total_seconds() // 3600)
    mins  = int((delta.total_seconds() % 3600) // 60)
    duration = f'{hours}h {mins}m' if hours else f'{mins} minutes'

    ctx = dict(
        title=instance.title,
        areas=instance.area,
        start_datetime=instance.start_datetime.strftime('%d %b %Y, %I:%M %p'),
        end_datetime=instance.end_datetime.strftime('%d %b %Y, %I:%M %p'),
        duration=duration,
        reason=instance.reason,
    )

    sent = 0
    for user in User.objects.filter(is_active=True):
        # Bell notification
        _notify(user, notif_type='warning',
            title=f'Planned Outage — {instance.area[:60]}',
            message=f'{instance.title} on {instance.start_datetime.strftime("%d %b %Y, %I:%M %p")}')
        # HTML email
        _html_email(user.email,
            subject=f'PowerGrid — Planned Outage on {instance.start_datetime.strftime("%d %b %Y")}',
            template='emails/outage_announcement.html',
            context=ctx)
        sent += 1

    # Mark as notified so we don't resend
    sender.objects.filter(pk=instance.pk).update(notified_at=timezone.now())
    print(f'[signals] Outage announcement sent to {sent} users')
