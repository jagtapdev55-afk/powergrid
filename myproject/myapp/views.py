 
from django.shortcuts import render, redirect
from django.contrib import messages

from accounts.models import Notification  # <--- CORRECT

from .utils import send_simple_email
from django.db.models import Count, Q
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required

from .models import (
    CommonForm, ConnectionRequest, BillPayment, Complaint,
    PowerOutage, MeterReading, FAQ, SupportTicket
)
from .forms import (
    ConnectionRequestForm, BillPaymentForm, ComplaintForm,
    PowerOutageForm, MeterReadingForm, SupportTicketForm
)
from myapp.utils import send_email
from django.utils import timezone

def home(request):
    return render(request, 'home.html')


def send_test_email(request):
    """
    Example: Send a test email
    """
    if request.method == 'POST':
        recipient_email = request.POST.get('email')
        
        success = send_simple_email(
            subject='Welcome to Admin Dashboard',
            message='Thank you for using our dashboard!',
            recipient_list=[recipient_email]
        )
        
        if success:
            messages.success(request, 'Email sent successfully!')
        else:
            messages.error(request, 'Failed to send email.')
        
        return redirect('home')
    
    return render(request, 'send_email.html')


def send_email_view(request):
    """Compatibility wrapper for URL imports that expect `send_email_view`."""
    return send_test_email(request)

# Create your views here.


#user dashboard all things rest......


from django.contrib.auth.decorators import login_required
from .models import CommonForm

# @login_required ensures only logged-in users can access this
@login_required
def user_dashboard(request):
    """
    This view handles the user dashboard page.
    It fetches data from database and sends it to the template.
    """
    
    # Get the current logged-in user
    user = request.user
    
    # Query the database for forms submitted by this user
    # We filter by email because forms are linked to email, not user object
    user_forms = CommonForm.objects.filter(
        email=user.email  # Find forms where email matches user's email
    ).order_by('-submitted_date')[:5]  # Get latest 5 forms, newest first
    
    # Count total forms by this user
    total_forms = CommonForm.objects.filter(email=user.email).count()
    
    # Count pending forms
    pending_forms = CommonForm.objects.filter(
        email=user.email,
        status='pending'  # Only pending status
    ).count()
    
    # Count approved forms
    approved_forms = CommonForm.objects.filter(
        email=user.email,
        status='approved'
    ).count()
    
    # If user is staff, they can also see forms assigned to them
    if user.is_staff:
        assigned_forms = CommonForm.objects.filter(
            assigned_to=user
        ).order_by('-submitted_date')[:5]
    else:
        assigned_forms = None  # Regular users don't have assigned forms
    
    # Package all data into a dictionary
    # This data will be available in the HTML template
    context = {
        'user': user,
        'user_forms': user_forms,
        'assigned_forms': assigned_forms,
        'total_forms': total_forms,
        'pending_forms': pending_forms,
        'approved_forms': approved_forms,
    }
    
    # Render the template with the data
    return render(request, 'dashboard/user_dashboard.html', context)

#user dasshboard views


@login_required
def user_dashboard(request):
    
    """Main dashboard for logged-in users"""
    user = request.user
    
    # Get user's submitted forms
    user_forms = CommonForm.objects.filter(
        email=user.email
    ).order_by('-submitted_date')[:5]
    
    # Count statistics
    total_forms = CommonForm.objects.filter(email=user.email).count()
    pending_forms = CommonForm.objects.filter(email=user.email, status='pending').count()
    approved_forms = CommonForm.objects.filter(email=user.email, status='approved').count()
    rejected_forms = CommonForm.objects.filter(email=user.email, status='rejected').count()
    
    # Connection requests stats
    total_connections = ConnectionRequest.objects.filter(user=user).count()
    pending_connections = ConnectionRequest.objects.filter(user=user, status='pending').count()
    
    # Complaints stats
    total_complaints = Complaint.objects.filter(user=user).count()
    resolved_complaints = Complaint.objects.filter(user=user, status='resolved').count()
    
    # Outage reports
    total_outages = PowerOutage.objects.filter(user=user).count()
    
    # Recent notifications
    notifications = Notification.objects.filter(user=user, is_read=False)[:5]
    unread_notifications_count = Notification.objects.filter(user=user, is_read=False).count()
    
    # Monthly activity (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        date = timezone.now() - timedelta(days=30*i)
        month_start = date.replace(day=1)
        if i == 0:
            month_end = timezone.now()
        else:
            next_month = month_start + timedelta(days=32)
            month_end = next_month.replace(day=1)
        
        count = CommonForm.objects.filter(
            email=user.email,
            submitted_date__gte=month_start,
            submitted_date__lt=month_end
        ).count()
        
        monthly_data.append({
            'month': month_start.strftime('%b'),
            'count': count
        })
    
    # If user is staff, get assigned forms
    if user.is_staff:
        assigned_forms = CommonForm.objects.filter(assigned_to=user).order_by('-submitted_date')[:5]
    else:
        assigned_forms = None
    
    context = {
        'user': user,
        'user_forms': user_forms,
        'assigned_forms': assigned_forms,
        'total_forms': total_forms,
        'pending_forms': pending_forms,
        'approved_forms': approved_forms,
        'rejected_forms': rejected_forms,
        'total_connections': total_connections,
        'pending_connections': pending_connections,
        'total_complaints': total_complaints,
        'resolved_complaints': resolved_complaints,
        'total_outages': total_outages,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
        'monthly_data': monthly_data,
    }
    
    return render(request, 'dashboard/user_dashboard.html', context)

# 1. NEW CONNECTION REQUEST
@login_required
def connection_request_view(request):
    """Submit new connection request"""
    if request.method == 'POST':
        form = ConnectionRequestForm(request.POST, request.FILES)
        if form.is_valid():
            connection = form.save(commit=False)
            connection.user = request.user
            connection.save()
            
            # Send confirmation email
            send_email(
                subject='Connection Request Received',
                message=f'''
Dear {connection.full_name},

Your connection request has been received successfully.

Request Number: {connection.request_number}
Connection Type: {connection.get_connection_type_display()}
Status: {connection.get_status_display()}

We will review your application and contact you within 3-5 business days.

Thank you for choosing PowerGrid!

Best regards,
PowerGrid Team
                ''',
                recipient_list=[connection.email]
            )
            
            messages.success(request, f'✅ Connection request submitted! Your request number is {connection.request_number}')
            return redirect('user_dashboard')
    else:
        # Pre-fill form with user data
        form = ConnectionRequestForm(initial={
            'full_name': request.user.get_full_name(),
            'email': request.user.email,
            'phone': request.user.phone if hasattr(request.user, 'phone') else ''
        })
    
    return render(request, 'services/connection_request.html', {'form': form})


# 2. BILL PAYMENT
@login_required
def bill_payment_view(request):
    """Pay electricity bill"""
    if request.method == 'POST':
        form = BillPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.user = request.user
            payment.paid_amount = payment.bill_amount  # Set paid amount same as bill amount
            payment.payment_status = 'pending'  # Initial status
            payment.save()
            
            # Send confirmation email
            send_email(
                subject='Bill Payment Initiated',
                message=f'''
Dear Customer,

Your bill payment has been initiated.

Payment ID: {payment.payment_id}
Consumer Number: {payment.consumer_number}
Amount: ₹{payment.paid_amount}
Status: {payment.get_payment_status_display()}

Your payment is being processed. You will receive a confirmation once completed.

Thank you!

Best regards,
PowerGrid Team
                ''',
                recipient_list=[request.user.email]
            )
            
            messages.success(request, f'✅ Payment initiated! Payment ID: {payment.payment_id}')
            return redirect('user_dashboard')
    else:
        form = BillPaymentForm()
    
    return render(request, 'services/bill_payment.html', {'form': form})


# 3. COMPLAINT REGISTRATION
@login_required
def complaint_registration_view(request):
    """Register a complaint"""
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.save()
            
            # Send confirmation email
            send_email(
                subject='Complaint Registered',
                message=f'''
Dear {complaint.full_name},

Your complaint has been registered successfully.

Complaint Number: {complaint.complaint_number}
Category: {complaint.get_category_display()}
Subject: {complaint.subject}
Status: {complaint.get_status_display()}

We will investigate your complaint and get back to you soon.

Thank you for your patience.

Best regards,
PowerGrid Support Team
                ''',
                recipient_list=[complaint.email]
            )
            
            messages.success(request, f'✅ Complaint registered! Complaint number: {complaint.complaint_number}')
            return redirect('user_dashboard')
    else:
        form = ComplaintForm(initial={
            'full_name': request.user.get_full_name(),
            'email': request.user.email,
            'phone': request.user.phone if hasattr(request.user, 'phone') else ''
        })
    
    return render(request, 'services/complaint_registration.html', {'form': form})


# 4. POWER OUTAGE REPORTING
@login_required
def power_outage_report_view(request):
    """Report power outage"""
    if request.method == 'POST':
        form = PowerOutageForm(request.POST)
        if form.is_valid():
            outage = form.save(commit=False)
            outage.user = request.user
            outage.save()
            
            # Send confirmation email
            send_email(
                subject='Power Outage Reported',
                message=f'''
Dear {outage.full_name},

Your power outage report has been received.

Report Number: {outage.report_number}
Outage Type: {outage.get_outage_type_display()}
Area: {outage.area}
Status: {outage.get_status_display()}

Our technical team has been notified and will work to restore power as soon as possible.

Thank you for reporting.

Best regards,
PowerGrid Technical Team
                ''',
                recipient_list=[request.user.email]
            )
            
            messages.success(request, f'✅ Outage reported! Report number: {outage.report_number}')
            return redirect('user_dashboard')
    else:
        form = PowerOutageForm(initial={
            'full_name': request.user.get_full_name(),
            'phone': request.user.phone if hasattr(request.user, 'phone') else '',
            'outage_start_time': timezone.now()
        })
    
    return render(request, 'services/power_outage_report.html', {'form': form})


# 5. METER READING SUBMISSION
@login_required
def meter_reading_submission_view(request):
    """Submit meter reading"""
    if request.method == 'POST':
        form = MeterReadingForm(request.POST, request.FILES)
        if form.is_valid():
            reading = form.save(commit=False)
            reading.user = request.user
            reading.save()
            
            # Send confirmation email
            send_email(
                subject='Meter Reading Submitted',
                message=f'''
Dear Customer,

Your meter reading has been submitted successfully.

Reading ID: {reading.reading_id}
Consumer Number: {reading.consumer_number}
Reading Date: {reading.reading_date}
Current Reading: {reading.current_reading}
Units Consumed: {reading.units_consumed}
Status: {reading.get_status_display()}

Your reading will be verified and your bill will be generated accordingly.

Thank you!

Best regards,
PowerGrid Billing Team
                ''',
                recipient_list=[request.user.email]
            )
            
            messages.success(request, f'✅ Meter reading submitted! Reading ID: {reading.reading_id}')
            return redirect('user_dashboard')
    else:
        form = MeterReadingForm(initial={
            'reading_date': timezone.now().date()
        })
    
    return render(request, 'services/meter_reading_submission.html', {'form': form})


# 6. FAQ VIEW
def faq_view(request):
    """Display FAQs grouped by category"""
    faqs = FAQ.objects.filter(is_active=True).order_by('category', 'order')
    
    # Group FAQs by category
    faq_categories = {}
    for faq in faqs:
        category = faq.get_category_display()
        if category not in faq_categories:
            faq_categories[category] = []
        faq_categories[category].append(faq)
    
    return render(request, 'services/faq.html', {'faq_categories': faq_categories})


# 7. SUPPORT TICKET
@login_required
def support_ticket_view(request):
    """Create support ticket"""
    if request.method == 'POST':
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            
            # Send confirmation email
            send_email(
                subject='Support Ticket Created',
                message=f'''
Dear {request.user.get_full_name() or request.user.username},

Your support ticket has been created successfully.

Ticket Number: {ticket.ticket_number}
Subject: {ticket.subject}
Priority: {ticket.get_priority_display()}
Status: {ticket.get_status_display()}

Our support team will respond to your ticket shortly.

Thank you!

Best regards,
PowerGrid Support Team
                ''',
                recipient_list=[request.user.email]
            )
            
            messages.success(request, f'✅ Ticket {ticket.ticket_number} created! Track it below.')
            return redirect('ticket_detail', ticket_id=ticket.pk)
    else:
        form = SupportTicketForm()
    
    return render(request, 'services/support_ticket.html', {'form': form})


# 8. MY APPLICATIONS VIEW
@login_required
def my_applications_view(request):
    """View all user's applications"""
    connection_requests = ConnectionRequest.objects.filter(user=request.user).order_by('-created_at')
    complaints = Complaint.objects.filter(user=request.user).order_by('-created_at')
    outage_reports = PowerOutage.objects.filter(user=request.user).order_by('-created_at')
    meter_readings = MeterReading.objects.filter(user=request.user).order_by('-created_at')
    support_tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'connection_requests': connection_requests,
        'complaints': complaints,
        'outage_reports': outage_reports,
        'meter_readings': meter_readings,
        'support_tickets': support_tickets,
    }
    
    return render(request, 'dashboard/my_applications.html', context)


#enhnaced version of dashboard
@login_required
def user_dashboard(request):
    """Enhanced dashboard with all 6 model querysets for template tables"""
    user = request.user

    # ── 6 model querysets for dashboard tables ──
    connection_requests = ConnectionRequest.objects.filter(user=user).order_by('-created_at')
    bill_payments       = BillPayment.objects.filter(user=user).order_by('-created_at')
    complaints          = Complaint.objects.filter(user=user).order_by('-created_at')
    outage_reports      = PowerOutage.objects.filter(user=user).order_by('-created_at')
    meter_readings      = MeterReading.objects.filter(user=user).order_by('-created_at')
    support_tickets     = SupportTicket.objects.filter(user=user).order_by('-created_at')

    # ── Stat counts ──
    connection_request_count = connection_requests.count()
    bill_payment_count       = bill_payments.count()
    complaint_count          = complaints.count()
    outage_report_count      = outage_reports.count()
    meter_reading_count      = meter_readings.count()
    support_ticket_count     = support_tickets.count()

    # Recent notifications
    notifications = Notification.objects.filter(user=user, is_read=False)[:5]
    unread_notifications_count = Notification.objects.filter(user=user, is_read=False).count()

    context = {
        'user': user,
        # querysets
        'connection_requests':      connection_requests[:5],
        'bill_payments':            bill_payments[:5],
        'complaints':               complaints[:4],
        'outage_reports':           outage_reports[:4],
        'meter_readings':           meter_readings[:4],
        'support_tickets':          support_tickets[:4],
        # counts
        'connection_request_count': connection_request_count,
        'bill_payment_count':       bill_payment_count,
        'complaint_count':          complaint_count,
        'outage_report_count':      outage_report_count,
        'meter_reading_count':      meter_reading_count,
        'support_ticket_count':     support_ticket_count,
        # notifications
        'notifications':            notifications,
        'unread_notifications_count': unread_notifications_count,
    }

    return render(request, 'dashboard/user_dashboard.html', context)

#seach function
@login_required
def my_applications_view(request):
    """View all user's applications with search and filter"""
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base querysets
    connection_requests = ConnectionRequest.objects.filter(user=request.user)
    complaints = Complaint.objects.filter(user=request.user)
    outage_reports = PowerOutage.objects.filter(user=request.user)
    meter_readings = MeterReading.objects.filter(user=request.user)
    support_tickets = SupportTicket.objects.filter(user=request.user)
    
    # Apply search
    if search_query:
        connection_requests = connection_requests.filter(
            Q(request_number__icontains=search_query) |
            Q(full_name__icontains=search_query)
        )
        complaints = complaints.filter(
            Q(complaint_number__icontains=search_query) |
            Q(subject__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter:
        connection_requests = connection_requests.filter(status=status_filter)
        complaints = complaints.filter(status=status_filter)
        outage_reports = outage_reports.filter(status=status_filter)
        meter_readings = meter_readings.filter(status=status_filter)
        support_tickets = support_tickets.filter(status=status_filter)
    
    # Apply date filter
    if date_from:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        connection_requests = connection_requests.filter(created_at__gte=date_from_obj)
        complaints = complaints.filter(created_at__gte=date_from_obj)
    
    if date_to:
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        connection_requests = connection_requests.filter(created_at__lte=date_to_obj)
        complaints = complaints.filter(created_at__lte=date_to_obj)
    
    # Order by most recent
    connection_requests = connection_requests.order_by('-created_at')
    complaints = complaints.order_by('-created_at')
    outage_reports = outage_reports.order_by('-created_at')
    meter_readings = meter_readings.order_by('-created_at')
    support_tickets = support_tickets.order_by('-created_at')
    
    context = {
        'connection_requests': connection_requests,
        'complaints': complaints,
        'outage_reports': outage_reports,
        'meter_readings': meter_readings,
        'support_tickets': support_tickets,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'dashboard/my_applications.html', context)

# ── FEATURE 4: Ticket Detail + Reply ──────────────────────────────────────
from django.shortcuts import get_object_or_404
from .models import TicketReply

@login_required
def ticket_detail_view(request, ticket_id):
    """Show full ticket thread + allow user to reply"""
    ticket = get_object_or_404(SupportTicket, pk=ticket_id, user=request.user)
    replies = ticket.replies.all()

    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        if message:
            TicketReply.objects.create(
                ticket=ticket,
                author=request.user,
                message=message,
                is_staff_reply=False,
            )
            # Notify: if ticket was awaiting_response, flip back to in_progress
            if ticket.status == 'awaiting_response':
                ticket.status = 'in_progress'
                ticket.save()

            # Notify assigned staff if any
            if ticket.assigned_to:
                Notification.objects.create(
                    user=ticket.assigned_to,
                    title=f'User replied on {ticket.ticket_number}',
                    message=f'{request.user.get_full_name() or request.user.username} replied: "{message[:80]}"',
                    notification_type='info',
                    link=f'/services/support/ticket/{ticket.pk}/',
                )
            messages.success(request, 'Reply sent.')
            return redirect('ticket_detail', ticket_id=ticket.pk)

    return render(request, 'services/ticket_detail.html', {
        'ticket': ticket,
        'replies': replies,
    })


# ══════════════════════════════════════════════════════════════
# FEATURE 1: PDF RECEIPT DOWNLOAD
# ══════════════════════════════════════════════════════════════
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io

@login_required
def download_payment_receipt(request, payment_id):
    """Generate and download PDF receipt for a bill payment."""
    from .models import BillPayment
    payment = get_object_or_404(BillPayment, payment_id=payment_id, user=request.user)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm)

    GREEN  = colors.HexColor('#3a9e25')
    BLACK  = colors.HexColor('#0d1117')
    GRAY   = colors.HexColor('#4a5568')
    LGRAY  = colors.HexColor('#f4f7fa')
    WHITE  = colors.white

    styles = getSampleStyleSheet()

    def sty(name, **kw):
        s = ParagraphStyle(name, **kw)
        return s

    title_sty  = sty('Title2',  fontSize=22, textColor=WHITE,     fontName='Helvetica-Bold', alignment=TA_LEFT)
    sub_sty    = sty('Sub',     fontSize=10, textColor=WHITE,      fontName='Helvetica',      alignment=TA_LEFT)
    h2_sty     = sty('H2',     fontSize=11, textColor=BLACK,       fontName='Helvetica-Bold', spaceAfter=4)
    label_sty  = sty('Label',  fontSize=9,  textColor=GRAY,        fontName='Helvetica',      spaceAfter=2)
    value_sty  = sty('Value',  fontSize=10, textColor=BLACK,       fontName='Helvetica-Bold', spaceAfter=6)
    amt_sty    = sty('Amt',    fontSize=20, textColor=GREEN,       fontName='Helvetica-Bold', alignment=TA_RIGHT)
    foot_sty   = sty('Foot',   fontSize=8,  textColor=GRAY,        fontName='Helvetica',      alignment=TA_CENTER)
    status_sty = sty('Status', fontSize=11, textColor=GREEN,       fontName='Helvetica-Bold', alignment=TA_CENTER)

    story = []

    # ── HEADER BANNER ──
    header_data = [[
        Paragraph('⚡ PowerGrid', title_sty),
        Paragraph(f'PAYMENT RECEIPT\n{payment.payment_id}', sty('R', fontSize=10, textColor=WHITE, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
    ]]
    header_table = Table(header_data, colWidths=[110*mm, 60*mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), GREEN),
        ('TOPPADDING',    (0,0), (-1,-1), 14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 14),
        ('LEFTPADDING',   (0,0), (-1,-1), 12),
        ('RIGHTPADDING',  (0,0), (-1,-1), 12),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8*mm))

    # ── STATUS BADGE ──
    status_color = GREEN if payment.payment_status == 'completed' else colors.HexColor('#e53e3e')
    status_label = payment.get_payment_status_display().upper()
    badge = Table([[Paragraph(f'● {status_label}', status_sty)]], colWidths=[170*mm])
    badge.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0fdf4') if payment.payment_status == 'completed' else colors.HexColor('#fff5f5')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('ROUNDEDCORNERS', [8]),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#d1fae5') if payment.payment_status == 'completed' else colors.HexColor('#fecaca')),
    ]))
    story.append(badge)
    story.append(Spacer(1, 6*mm))

    # ── AMOUNT ──
    story.append(Paragraph(f'Rs {payment.paid_amount}', amt_sty))
    story.append(Paragraph(f'For billing month: {payment.billing_month}', sty('bm', fontSize=9, textColor=GRAY, fontName='Helvetica', alignment=TA_RIGHT)))
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#e8edf2')))
    story.append(Spacer(1, 6*mm))

    # ── PAYMENT DETAILS TABLE ──
    story.append(Paragraph('Payment Details', h2_sty))
    story.append(Spacer(1, 3*mm))

    def row(label, value):
        return [
            Paragraph(label, sty('lbl', fontSize=9, textColor=GRAY, fontName='Helvetica')),
            Paragraph(str(value), sty('val', fontSize=9, textColor=BLACK, fontName='Helvetica-Bold')),
        ]

    details = [
        row('Payment ID',       payment.payment_id),
        row('Consumer Number',  payment.consumer_number),
        row('Billing Month',    payment.billing_month),
        row('Bill Amount',      f'Rs {payment.bill_amount}'),
        row('Late Fee',         f'Rs {payment.late_fee}'),
        row('Discount',         f'Rs {payment.discount}'),
        row('Amount Paid',      f'Rs {payment.paid_amount}'),
        row('Payment Method',   payment.get_payment_method_display()),
        row('Payment Status',   payment.get_payment_status_display()),
        row('Transaction ID',   payment.transaction_id or '—'),
        row('Payment Date',     payment.payment_date.strftime('%d %b %Y, %I:%M %p') if payment.payment_date else '—'),
        row('Receipt Generated', payment.created_at.strftime('%d %b %Y, %I:%M %p')),
    ]

    detail_table = Table(details, colWidths=[70*mm, 100*mm])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), WHITE),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [WHITE, LGRAY]),
        ('TOPPADDING',    (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('RIGHTPADDING',  (0,0), (-1,-1), 10),
        ('BOX',     (0,0), (-1,-1), 1, colors.HexColor('#e8edf2')),
        ('LINEBELOW', (0,0), (-1,-2), 0.5, colors.HexColor('#e8edf2')),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 6*mm))

    # ── ACCOUNT HOLDER ──
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#e8edf2')))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('Account Holder', h2_sty))
    acct = Table([
        row('Name',     payment.user.get_full_name() or payment.user.username),
        row('Email',    payment.user.email),
        row('Username', payment.user.username),
    ], colWidths=[70*mm, 100*mm])
    acct.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [WHITE, LGRAY]),
        ('TOPPADDING',    (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('RIGHTPADDING',  (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e8edf2')),
        ('LINEBELOW', (0,0), (-1,-2), 0.5, colors.HexColor('#e8edf2')),
    ]))
    story.append(acct)
    story.append(Spacer(1, 10*mm))

    # ── FOOTER ──
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#e8edf2')))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('This is a computer-generated receipt and does not require a signature.', foot_sty))
    story.append(Paragraph('PowerGrid Electricity Services  |  support@powergrid.com  |  1800-XXX-XXXX', foot_sty))

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="PowerGrid_Receipt_{payment.payment_id}.pdf"'
    return response


# ── FEATURE 3+4: Outage Announcements Page ────────────────────────────────
from .models import OutageAnnouncement

def outage_announcements_view(request):
    """Public page listing all upcoming and recent outage announcements."""
    announcements = OutageAnnouncement.objects.all().order_by('-start_datetime')[:20]
    return render(request, 'services/outage_announcements.html', {
        'announcements': announcements
    })
