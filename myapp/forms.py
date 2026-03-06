from django import forms
from .models import (
    ConnectionRequest, BillPayment, Complaint,
    PowerOutage, MeterReading, SupportTicket
)

# 1. CONNECTION REQUEST FORM
class ConnectionRequestForm(forms.ModelForm):
    class Meta:
        model = ConnectionRequest
        fields = [
            'full_name', 'phone', 'email', 'alternate_phone',
            'address_line1', 'address_line2', 'city', 'state', 'pincode', 'landmark',
            'connection_type', 'estimated_load', 'purpose',
            'property_ownership', 'property_type',
            'id_proof', 'address_proof', 'property_document'
        ]
        
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your full name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+91 XXXXX XXXXX'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'your.email@example.com'
            }),
            'alternate_phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Alternate phone (optional)'
            }),
            'address_line1': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'House/Flat number, Building name'
            }),
            'address_line2': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Street, Area (optional)'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'State'
            }),
            'pincode': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '000000'
            }),
            'landmark': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nearby landmark (optional)'
            }),
            'connection_type': forms.Select(attrs={'class': 'form-input'}),
            'estimated_load': forms.Select(attrs={'class': 'form-input'}),
            'property_ownership': forms.Select(attrs={'class': 'form-input'}),
            'property_type': forms.Select(attrs={'class': 'form-input'}),
            'purpose': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Describe the purpose of connection',
                'rows': 4
            }),
        }


# 2. BILL PAYMENT FORM
class BillPaymentForm(forms.ModelForm):
    class Meta:
        model = BillPayment
        fields = [
            'consumer_number', 'billing_month', 'bill_amount',
            'payment_method'
        ]
        
        widgets = {
            'consumer_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your consumer number'
            }),
            'billing_month': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., January 2025'
            }),
            'bill_amount': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-input'}),
        }


# 3. COMPLAINT FORM
class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = [
            'full_name', 'phone', 'email', 'consumer_number',
            'category', 'subject', 'description',
            'address', 'landmark',
            'attachment1', 'attachment2'
        ]
        
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your full name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+91 XXXXX XXXXX'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'your.email@example.com'
            }),
            'consumer_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Consumer number (optional)'
            }),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'subject': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Brief subject of complaint'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Describe your complaint in detail',
                'rows': 5
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Full address',
                'rows': 3
            }),
            'landmark': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nearby landmark (optional)'
            }),
        }


# 4. POWER OUTAGE FORM
class PowerOutageForm(forms.ModelForm):
    class Meta:
        model = PowerOutage
        fields = [
            'full_name', 'phone', 'consumer_number',
            'outage_type', 'outage_start_time',
            'area', 'address', 'landmark',
            'description', 'affected_households'
        ]
        
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your full name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+91 XXXXX XXXXX'
            }),
            'consumer_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Consumer number (optional)'
            }),
            'outage_type': forms.Select(attrs={'class': 'form-input'}),
            'outage_start_time': forms.DateTimeInput(attrs={
                'class': 'form-input',
                'type': 'datetime-local'
            }),
            'area': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Area/Locality'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Full address',
                'rows': 3
            }),
            'landmark': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nearby landmark (optional)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Additional details (optional)',
                'rows': 3
            }),
            'affected_households': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '1'
            }),
        }


# 5. METER READING FORM
class MeterReadingForm(forms.ModelForm):
    class Meta:
        model = MeterReading
        fields = [
            'consumer_number', 'reading_date',
            'current_reading', 'previous_reading',
            'meter_number', 'meter_photo'
        ]
        
        widgets = {
            'consumer_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your consumer number'
            }),
            'reading_date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'current_reading': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'previous_reading': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'meter_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Meter number'
            }),
        }


# 6. SUPPORT TICKET FORM
class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['subject', 'description', 'priority']
        
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Brief subject of your query'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Describe your issue or question',
                'rows': 5
            }),
            'priority': forms.Select(attrs={'class': 'form-input'}),
        }