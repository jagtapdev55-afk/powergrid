"""
serializers.py
Converts Django model instances ↔ JSON for the REST API.
Think of it like a translator between Python objects and JSON data.
"""

from rest_framework import serializers
from myapp.models import (
    MeterReading, BillPayment, ConnectionRequest,
    Complaint, PowerOutage, SupportTicket
)


# ── METER READING ──────────────────────────────────────────────────────────

class MeterReadingSerializer(serializers.ModelSerializer):
    """Used to READ meter reading data (GET requests)."""

    source_display = serializers.CharField(
        source='get_source_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model  = MeterReading
        fields = [
            'reading_id', 'consumer_number', 'reading_date',
            'current_reading', 'previous_reading', 'units_consumed',
            'meter_number', 'source', 'source_display',
            'status', 'status_display',
            # Smart meter fields
            'voltage', 'current_amp', 'power_factor',
            'tamper_alert', 'signal_strength', 'device_id', 'auto_verified',
            'created_at',
        ]
        read_only_fields = [
            'reading_id', 'units_consumed', 'auto_verified', 'created_at'
        ]


class SmartMeterSubmitSerializer(serializers.Serializer):
    """
    Used when a SMART METER (or any device) POSTs a reading.
    This is the main API endpoint for future smart meter integration.

    Example POST body:
    {
        "consumer_number": "CON001",
        "device_id": "SM-MH-00123",
        "current_reading": 1456.7,
        "previous_reading": 1411.4,
        "reading_date": "2026-03-09",
        "voltage": 231.4,
        "current_amp": 4.2,
        "power_factor": 0.92,
        "signal_strength": 87,
        "tamper_alert": false,
        "source": "smart_meter",
        "api_key": "your-secret-key"
    }
    """

    # Required fields
    consumer_number  = serializers.CharField(max_length=50)
    current_reading  = serializers.DecimalField(max_digits=10, decimal_places=2)
    previous_reading = serializers.DecimalField(max_digits=10, decimal_places=2)
    reading_date     = serializers.DateField()
    api_key          = serializers.CharField(write_only=True)

    # Optional — filled by smart meter, empty for manual
    device_id        = serializers.CharField(max_length=100, required=False, allow_null=True)
    voltage          = serializers.FloatField(required=False, allow_null=True)
    current_amp      = serializers.FloatField(required=False, allow_null=True)
    power_factor     = serializers.FloatField(required=False, allow_null=True)
    signal_strength  = serializers.IntegerField(required=False, allow_null=True)
    tamper_alert     = serializers.BooleanField(required=False, default=False)
    source           = serializers.ChoiceField(
        choices=['manual', 'photo', 'field_worker', 'smart_meter'],
        default='smart_meter'
    )

    def validate_current_reading(self, value):
        if value < 0:
            raise serializers.ValidationError("Reading cannot be negative.")
        return value

    def validate(self, data):
        if data['current_reading'] < data['previous_reading']:
            raise serializers.ValidationError(
                "Current reading cannot be less than previous reading."
            )
        return data


# ── BILL PAYMENT ───────────────────────────────────────────────────────────

class BillPaymentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source='get_payment_status_display', read_only=True
    )

    class Meta:
        model  = BillPayment
        fields = [
            'payment_id', 'consumer_number', 'billing_month',
            'bill_amount', 'paid_amount', 'late_fee', 'discount',
            'payment_method', 'payment_status', 'status_display',
            'transaction_id', 'payment_date', 'created_at',
        ]
        read_only_fields = ['payment_id', 'created_at']


# ── CONNECTION REQUEST ─────────────────────────────────────────────────────

class ConnectionRequestSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model  = ConnectionRequest
        fields = [
            'request_number', 'full_name', 'connection_type',
            'status', 'status_display', 'created_at',
        ]
        read_only_fields = ['request_number', 'created_at']


# ── COMPLAINT ──────────────────────────────────────────────────────────────

class ComplaintSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model  = Complaint
        fields = [
            'complaint_number', 'subject', 'category',
            'status', 'status_display', 'priority', 'created_at',
        ]
        read_only_fields = ['complaint_number', 'created_at']


# ── POWER OUTAGE ───────────────────────────────────────────────────────────

class PowerOutageSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model  = PowerOutage
        fields = [
            'report_number', 'area', 'outage_type',
            'status', 'status_display', 'created_at',
        ]
        read_only_fields = ['report_number', 'created_at']


# ── SUPPORT TICKET ─────────────────────────────────────────────────────────

class SupportTicketSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model  = SupportTicket
        fields = [
            'ticket_number', 'subject', 'priority',
            'status', 'status_display', 'created_at',
        ]
        read_only_fields = ['ticket_number', 'created_at']
