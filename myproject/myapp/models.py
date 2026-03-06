from django.db import models
from django.conf import settings
from django.utils import timezone 
# myapp/models.py



class CommonForm(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Auto-generated form number
    form_number = models.CharField(max_length=50, unique=True, editable=False)
    
    # Basic applicant details
    name = models.CharField(max_length=200, verbose_name='Full Name')
    phone = models.CharField(max_length=15, verbose_name='Phone Number')
    email = models.EmailField(verbose_name='Email Address')
    address = models.TextField(verbose_name='Address')
    
    # Form details
    subject = models.CharField(max_length=200, verbose_name='Subject/Purpose', blank=True)
    description = models.TextField(verbose_name='Description/Details', blank=True)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Timestamps
    submitted_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    # Optional: Assigned staff
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_forms')
    
    # Admin remarks
    remarks = models.TextField(blank=True, verbose_name='Admin Remarks')
    
    class Meta:
        ordering = ['-submitted_date']
        verbose_name = 'Common Form'
        verbose_name_plural = 'Common Forms'
    
    def save(self, *args, **kwargs):
        # Auto-generate form number if not exists
        if not self.form_number:
            # Get last form number
            last_form = CommonForm.objects.all().order_by('id').last()
            if last_form:
                last_number = int(last_form.form_number.replace('FORM', ''))
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.form_number = f'FORM{new_number:04d}'  # FORM0001, FORM0002, etc.
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.form_number} - {self.name}"

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Article(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    published_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    
    

# Create your models here.
# 1. NEW CONNECTION REQUEST MODEL
class ConnectionRequest(models.Model):
    CONNECTION_TYPE_CHOICES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
    ]
    
    LOAD_CHOICES = [
        ('1-5', '1-5 KW'),
        ('5-10', '5-10 KW'),
        ('10-20', '10-20 KW'),
        ('20-50', '20-50 KW'),
        ('50+', '50+ KW'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('site_inspection', 'Site Inspection Scheduled'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Connection Completed'),
    ]
    
    # Auto-generated request number
    request_number = models.CharField(max_length=50, unique=True, editable=False)
    
    # User information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='connection_requests')
    
    # Applicant Details
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    alternate_phone = models.CharField(max_length=15, blank=True)
    
    # Address Details
    address_line1 = models.CharField(max_length=300)
    address_line2 = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    landmark = models.CharField(max_length=200, blank=True)
    
    # Connection Details
    connection_type = models.CharField(max_length=20, choices=CONNECTION_TYPE_CHOICES)
    estimated_load = models.CharField(max_length=20, choices=LOAD_CHOICES)
    purpose = models.TextField(help_text="Purpose of connection")
    
    # Property Details
    property_ownership = models.CharField(max_length=50, choices=[
        ('owned', 'Owned'),
        ('rented', 'Rented'),
    ])
    property_type = models.CharField(max_length=50, choices=[
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('shop', 'Shop'),
        ('office', 'Office'),
        ('factory', 'Factory'),
        ('other', 'Other'),
    ])
    
    # Documents (Optional - for file uploads)
    id_proof = models.FileField(upload_to='connection_requests/id_proof/', blank=True, null=True)
    address_proof = models.FileField(upload_to='connection_requests/address_proof/', blank=True, null=True)
    property_document = models.FileField(upload_to='connection_requests/property_docs/', blank=True, null=True)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    inspection_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    
    # Admin fields
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_connection_requests')
    admin_remarks = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Connection Request'
        verbose_name_plural = 'Connection Requests'
        # ADD THESE INDEXES FOR BETTER PERFORMANCE:
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.request_number:
            # Auto-generate request number: CONN2025001
            last_request = ConnectionRequest.objects.all().order_by('id').last()
            if last_request:
                last_number = int(last_request.request_number.replace('CONN', ''))
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.request_number = f'CONN{new_number:07d}'
        
        super().save(*args, **kwargs)
    

    def get_timeline_steps(self):
        order = ['pending', 'under_review', 'site_inspection', 'approved', 'completed']
        labels = {'pending':'Pending','under_review':'Under Review','site_inspection':'Inspection',
                  'approved':'Approved','completed':'Completed'}
        if self.status == 'rejected':
            return [{'label': s_label, 'done': True, 'active': False}
                    for s, s_label in labels.items() if order.index(s) < order.index('approved')] +                    [{'label': 'Rejected', 'done': False, 'active': True}]
        steps = []
        reached = False
        for s in order:
            if s == self.status:
                steps.append({'label': labels[s], 'done': False, 'active': True})
                reached = True
            elif not reached:
                steps.append({'label': labels[s], 'done': True, 'active': False})
            else:
                steps.append({'label': labels[s], 'done': False, 'active': False})
        return steps

    def __str__(self):
        return f"{self.request_number} - {self.full_name}"
    



# 2. BILL PAYMENT MODEL
class BillPayment(models.Model):
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('online', 'Online Payment'),
        ('upi', 'UPI'),
        ('card', 'Credit/Debit Card'),
        ('netbanking', 'Net Banking'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
    ]
    
    # Auto-generated payment ID
    payment_id = models.CharField(max_length=50, unique=True, editable=False)
    
    # User and bill details
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bill_payments')
    consumer_number = models.CharField(max_length=50)
    billing_month = models.CharField(max_length=20, help_text="e.g., January 2025")
    
    # Amount details
    bill_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Payment information
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Additional details
    remarks = models.TextField(blank=True)
    receipt_generated = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Bill Payment'
        verbose_name_plural = 'Bill Payments'  # ✅ Unique - NOT "Connection Requests"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['payment_status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.payment_id:
            # Auto-generate payment ID: PAY2025001
            last_payment = BillPayment.objects.all().order_by('id').last()
            if last_payment:
                last_number = int(last_payment.payment_id.replace('PAY', ''))
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.payment_id = f'PAY{new_number:07d}'
        
        # Set payment date when status becomes completed
        if self.payment_status == 'completed' and not self.payment_date:
            self.payment_date = timezone.now()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.payment_id} - {self.consumer_number} - ₹{self.paid_amount}"


# 3. COMPLAINT REGISTRATION MODEL
class Complaint(models.Model):
    CATEGORY_CHOICES = [
        ('billing', 'Billing Issue'),
        ('power_cut', 'Unscheduled Power Cut'),
        ('voltage', 'Low/High Voltage'),
        ('meter', 'Meter Issue'),
        ('connection', 'Connection Problem'),
        ('street_light', 'Street Light'),
        ('staff_behavior', 'Staff Behavior'),
        ('other', 'Other'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('registered', 'Registered'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('reopened', 'Reopened'),
    ]
    
    # Auto-generated complaint number
    complaint_number = models.CharField(max_length=50, unique=True, editable=False)
    
    # User information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='complaints')
    consumer_number = models.CharField(max_length=50, blank=True)
    
    # Complaint details
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    subject = models.CharField(max_length=300)
    description = models.TextField()
    
    # Location
    address = models.TextField()
    landmark = models.CharField(max_length=200, blank=True)
    
    # Attachments
    attachment1 = models.FileField(upload_to='complaints/', blank=True, null=True)
    attachment2 = models.FileField(upload_to='complaints/', blank=True, null=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='registered')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Admin fields
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    resolution_details = models.TextField(blank=True)
    resolved_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Complaint'
        verbose_name_plural = 'Complaints'  # ✅ Unique
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.complaint_number:
            # Auto-generate complaint number: COMP2025001
            last_complaint = Complaint.objects.all().order_by('id').last()
            if last_complaint:
                last_number = int(last_complaint.complaint_number.replace('COMP', ''))
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.complaint_number = f'COMP{new_number:07d}'
        
        super().save(*args, **kwargs)
    

    def get_timeline_steps(self):
        order  = ['registered', 'acknowledged', 'in_progress', 'resolved', 'closed']
        labels = {'registered':'Registered','acknowledged':'Acknowledged',
                  'in_progress':'In Progress','resolved':'Resolved','closed':'Closed'}
        if self.status == 'reopened':
            return [{'label':'Registered','done':True,'active':False},
                    {'label':'Resolved','done':True,'active':False},
                    {'label':'Reopened','done':False,'active':True}]
        steps = []
        reached = False
        for s in order:
            if s == self.status:
                steps.append({'label': labels[s], 'done': False, 'active': True})
                reached = True
            elif not reached:
                steps.append({'label': labels[s], 'done': True, 'active': False})
            else:
                steps.append({'label': labels[s], 'done': False, 'active': False})
        return steps

    def __str__(self):
        return f"{self.complaint_number} - {self.subject}"


# 4. POWER OUTAGE REPORT MODEL
class PowerOutage(models.Model):
    STATUS_CHOICES = [
        ('reported', 'Reported'),
        ('acknowledged', 'Acknowledged'),
        ('investigating', 'Investigating'),
        ('repairing', 'Repairing'),
        ('resolved', 'Resolved'),
    ]
    
    OUTAGE_TYPE_CHOICES = [
        ('complete', 'Complete Power Cut'),
        ('partial', 'Partial Power Cut'),
        ('fluctuation', 'Voltage Fluctuation'),
    ]
    
    # Auto-generated report number
    report_number = models.CharField(max_length=50, unique=True, editable=False)
    
    # User information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='power_outages')
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    consumer_number = models.CharField(max_length=50, blank=True)
    
    # Outage details
    outage_type = models.CharField(max_length=20, choices=OUTAGE_TYPE_CHOICES)
    outage_start_time = models.DateTimeField()
    outage_end_time = models.DateTimeField(null=True, blank=True)
    
    # Location
    area = models.CharField(max_length=200)
    address = models.TextField()
    landmark = models.CharField(max_length=200, blank=True)
    
    # Additional information
    description = models.TextField(blank=True)
    affected_households = models.IntegerField(default=1, help_text="Estimated number of affected households")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reported')
    
    # Admin fields
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_outages')
    cause = models.TextField(blank=True, help_text="Cause of outage")
    resolution_details = models.TextField(blank=True)
    estimated_resolution_time = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Power Outage Report'
        verbose_name_plural = 'Power Outage Reports'  # ✅ Unique
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.report_number:
            # Auto-generate report number: OUT2025001
            last_report = PowerOutage.objects.all().order_by('id').last()
            if last_report:
                last_number = int(last_report.report_number.replace('OUT', ''))
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.report_number = f'OUT{new_number:07d}'
        
        super().save(*args, **kwargs)
    

    def get_timeline_steps(self):
        order  = ['reported', 'acknowledged', 'investigating', 'repairing', 'resolved']
        labels = {'reported':'Reported','acknowledged':'Acknowledged',
                  'investigating':'Investigating','repairing':'Repairing','resolved':'Resolved'}
        steps = []
        reached = False
        for s in order:
            if s == self.status:
                steps.append({'label': labels[s], 'done': False, 'active': True})
                reached = True
            elif not reached:
                steps.append({'label': labels[s], 'done': True, 'active': False})
            else:
                steps.append({'label': labels[s], 'done': False, 'active': False})
        return steps

    def __str__(self):
        return f"{self.report_number} - {self.area}"


# 5. METER READING SUBMISSION MODEL
class MeterReading(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('billed', 'Billed'),
    ]
    
    # Auto-generated reading ID
    reading_id = models.CharField(max_length=50, unique=True, editable=False)
    
    # User information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='meter_readings')
    consumer_number = models.CharField(max_length=50)
    
    # Reading details
    reading_date = models.DateField()
    current_reading = models.DecimalField(max_digits=10, decimal_places=2)
    previous_reading = models.DecimalField(max_digits=10, decimal_places=2)
    units_consumed = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    
    # Meter details
    meter_number = models.CharField(max_length=50)
    meter_photo = models.ImageField(upload_to='meter_readings/', blank=True, null=True, help_text="Upload photo of meter reading")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    
    # Admin verification
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_readings')
    verification_date = models.DateTimeField(null=True, blank=True)
    admin_remarks = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Meter Reading'
        verbose_name_plural = 'Meter Readings'  # ✅ Unique
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]

    
    def save(self, *args, **kwargs):
        if not self.reading_id:
            # Auto-generate reading ID: READ2025001
            last_reading = MeterReading.objects.all().order_by('id').last()
            if last_reading:
                last_number = int(last_reading.reading_id.replace('READ', ''))
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.reading_id = f'READ{new_number:07d}'
        
        # Calculate units consumed
        self.units_consumed = self.current_reading - self.previous_reading
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.reading_id} - {self.consumer_number} - {self.units_consumed} units"


# 6. FAQ MODEL
class FAQ(models.Model):
    CATEGORY_CHOICES = [
        ('billing', 'Billing & Payments'),
        ('connection', 'New Connection'),
        ('technical', 'Technical Issues'),
        ('meter', 'Meter Related'),
        ('general', 'General'),
    ]
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    question = models.CharField(max_length=500)
    answer = models.TextField()
    order = models.IntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'  # ✅ Unique
        ordering = ['category', 'order']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.question


# 7. SUPPORT TICKET MODEL
class SupportTicket(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('awaiting_response', 'Awaiting Response'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    # Auto-generated ticket number
    ticket_number = models.CharField(max_length=50, unique=True, editable=False)
    
    # User information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='support_tickets')
    
    # Ticket details
    subject = models.CharField(max_length=300)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Admin fields
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    resolution = models.TextField(blank=True)
    resolved_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Support Ticket'
        verbose_name_plural = 'Support Tickets'  # ✅ Unique
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Auto-generate ticket number: TICK2025001
            last_ticket = SupportTicket.objects.all().order_by('id').last()
            if last_ticket:
                last_number = int(last_ticket.ticket_number.replace('TICK', ''))
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.ticket_number = f'TICK{new_number:07d}'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"



# 8. TICKET REPLY MODEL — admin and user can exchange messages on a ticket
class TicketReply(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    is_staff_reply = models.BooleanField(default=False)  # True = admin reply, False = user reply
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Ticket Reply'
        verbose_name_plural = 'Ticket Replies'

    def __str__(self):
        who = 'Staff' if self.is_staff_reply else 'User'
        return f'{who} reply on {self.ticket.ticket_number} at {self.created_at:%Y-%m-%d %H:%M}'


# ── FEATURE 4: SCHEDULED OUTAGE ANNOUNCEMENT ──────────────────────────────
class OutageAnnouncement(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('ongoing',   'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    title           = models.CharField(max_length=300)
    area            = models.CharField(max_length=300, help_text='Comma-separated areas affected')
    reason          = models.TextField(help_text='Reason for the planned outage')
    start_datetime  = models.DateTimeField()
    end_datetime    = models.DateTimeField()
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notify_users    = models.BooleanField(default=True, help_text='Send email notification to all users')
    notified_at     = models.DateTimeField(null=True, blank=True)
    created_by      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_datetime']
        verbose_name = 'Outage Announcement'
        verbose_name_plural = 'Outage Announcements'

    def __str__(self):
        return f'{self.title} — {self.start_datetime.strftime("%d %b %Y")}'
