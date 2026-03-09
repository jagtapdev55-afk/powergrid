"""
api/views.py
All REST API endpoints for PowerGrid.

These are the "doors" that smart meters, mobile apps,
or any external system can use to talk to your Django system.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from myapp.models import (
    MeterReading, BillPayment, ConnectionRequest,
    Complaint, PowerOutage, SupportTicket
)
from .serializers import (
    MeterReadingSerializer, SmartMeterSubmitSerializer,
    BillPaymentSerializer, ConnectionRequestSerializer,
    ComplaintSerializer, PowerOutageSerializer, SupportTicketSerializer,
)

User = get_user_model()

# ── API KEY (Simple security for smart meter) ──────────────────────────────
# In production this would be in .env file
# Smart meter must send this key to prove it's authorised
SMART_METER_API_KEY = getattr(settings, 'SMART_METER_API_KEY', 'powergrid-smart-meter-secret-2026')


# ══════════════════════════════════════════════════════════════════════════
# 1. SMART METER READING ENDPOINT
# The most important endpoint — this is where smart meters POST their data
# ══════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([AllowAny])  # No login needed — uses API key instead
def submit_meter_reading(request):
    """
    POST /api/meter-reading/submit/

    Smart meter or any device sends reading here.
    
    Example request body:
    {
        "consumer_number": "CON0000001",
        "current_reading": 1456.7,
        "previous_reading": 1411.4,
        "reading_date": "2026-03-09",
        "device_id": "SM-MH-00123",
        "voltage": 231.4,
        "current_amp": 4.2,
        "power_factor": 0.92,
        "signal_strength": 87,
        "tamper_alert": false,
        "source": "smart_meter",
        "api_key": "powergrid-smart-meter-secret-2026"
    }
    """

    serializer = SmartMeterSubmitSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    # ── Verify API key ──
    if data['api_key'] != SMART_METER_API_KEY:
        return Response({
            'success': False,
            'error': 'Invalid API key. Access denied.'
        }, status=status.HTTP_401_UNAUTHORIZED)

    # ── Find the user linked to this consumer number ──
    try:
        from accounts.models import ConsumerNumber
        consumer_obj = ConsumerNumber.objects.get(
            consumer_number=data['consumer_number']
        )
        user = consumer_obj.user
    except Exception:
        # If consumer number not found, still save but without user link
        user = None

    if user is None:
        return Response({
            'success': False,
            'error': f"Consumer number {data['consumer_number']} not found in system."
        }, status=status.HTTP_404_NOT_FOUND)

    # ── Determine if auto-verified (smart meter readings skip manual review) ──
    source       = data.get('source', 'smart_meter')
    auto_verified = source == 'smart_meter'

    # ── Generate reading ID ──
    last = MeterReading.objects.all().order_by('id').last()
    new_number = int(last.reading_id.replace('READ', '')) + 1 if last else 1
    reading_id = f'READ{new_number:07d}'

    # ── Create the reading ──
    reading = MeterReading.objects.create(
        reading_id       = reading_id,
        user             = user,
        consumer_number  = data['consumer_number'],
        reading_date     = data['reading_date'],
        current_reading  = data['current_reading'],
        previous_reading = data['previous_reading'],
        meter_number     = data.get('device_id', 'SMART-METER'),
        source           = source,
        device_id        = data.get('device_id'),
        voltage          = data.get('voltage'),
        current_amp      = data.get('current_amp'),
        power_factor     = data.get('power_factor'),
        signal_strength  = data.get('signal_strength'),
        tamper_alert     = data.get('tamper_alert', False),
        auto_verified    = auto_verified,
        status           = 'verified' if auto_verified else 'submitted',
    )

    # ── Alert if tamper detected ──
    if reading.tamper_alert:
        # Create a complaint automatically
        Complaint.objects.create(
            user            = user,
            consumer_number = data['consumer_number'],
            full_name       = user.get_full_name() or user.username,
            phone           = getattr(user, 'phone', ''),
            email           = user.email,
            category        = 'meter',
            subject         = f'TAMPER ALERT — Smart Meter {data.get("device_id", "")}',
            description     = f'Automatic tamper alert received from smart meter device {data.get("device_id")} at {timezone.now()}',
            priority        = 'urgent',
            status          = 'registered',
        )

    return Response({
        'success'      : True,
        'reading_id'   : reading.reading_id,
        'consumer'     : reading.consumer_number,
        'units_consumed': str(reading.units_consumed),
        'source'       : source,
        'auto_verified': auto_verified,
        'tamper_alert' : reading.tamper_alert,
        'message'      : 'Reading received and auto-verified.' if auto_verified else 'Reading received. Pending admin verification.',
    }, status=status.HTTP_201_CREATED)


# ══════════════════════════════════════════════════════════════════════════
# 2. CONSUMER STATUS API
# Check status of any application by reference number
# ══════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def consumer_status(request):
    """
    GET /api/status/?type=payment&ref=PAY0000001
    GET /api/status/?type=complaint&ref=COMP0000001
    GET /api/status/?type=connection&ref=CONN0000001
    GET /api/status/?type=ticket&ref=TICK0000001
    GET /api/status/?type=outage&ref=OUT0000001
    GET /api/status/?type=meter&ref=READ0000001

    Returns current status of any application.
    Useful for mobile apps to check status without opening browser.
    """

    ref_type = request.GET.get('type', '').lower()
    ref      = request.GET.get('ref', '').strip()

    if not ref_type or not ref:
        return Response({
            'error': 'Both type and ref parameters required.',
            'example': '/api/status/?type=payment&ref=PAY0000001'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        if ref_type == 'payment':
            obj = BillPayment.objects.get(payment_id=ref, user=request.user)
            return Response({
                'reference'  : obj.payment_id,
                'type'       : 'Bill Payment',
                'status'     : obj.payment_status,
                'status_label': obj.get_payment_status_display(),
                'amount'     : str(obj.paid_amount),
                'updated_at' : obj.updated_at,
            })

        elif ref_type == 'complaint':
            obj = Complaint.objects.get(complaint_number=ref, user=request.user)
            return Response({
                'reference'  : obj.complaint_number,
                'type'       : 'Complaint',
                'status'     : obj.status,
                'status_label': obj.get_status_display(),
                'subject'    : obj.subject,
                'updated_at' : obj.updated_at,
            })

        elif ref_type == 'connection':
            obj = ConnectionRequest.objects.get(request_number=ref, user=request.user)
            return Response({
                'reference'  : obj.request_number,
                'type'       : 'Connection Request',
                'status'     : obj.status,
                'status_label': obj.get_status_display(),
                'updated_at' : obj.updated_at,
            })

        elif ref_type == 'ticket':
            obj = SupportTicket.objects.get(ticket_number=ref, user=request.user)
            return Response({
                'reference'  : obj.ticket_number,
                'type'       : 'Support Ticket',
                'status'     : obj.status,
                'status_label': obj.get_status_display(),
                'subject'    : obj.subject,
                'updated_at' : obj.updated_at,
            })

        elif ref_type == 'outage':
            obj = PowerOutage.objects.get(report_number=ref, user=request.user)
            return Response({
                'reference'  : obj.report_number,
                'type'       : 'Power Outage Report',
                'status'     : obj.status,
                'status_label': obj.get_status_display(),
                'area'       : obj.area,
                'updated_at' : obj.updated_at,
            })

        elif ref_type == 'meter':
            obj = MeterReading.objects.get(reading_id=ref, user=request.user)
            return Response({
                'reference'    : obj.reading_id,
                'type'         : 'Meter Reading',
                'status'       : obj.status,
                'status_label' : obj.get_status_display(),
                'units_consumed': str(obj.units_consumed),
                'source'       : obj.source,
                'auto_verified': obj.auto_verified,
                'updated_at'   : obj.updated_at,
            })

        else:
            return Response({
                'error': f'Unknown type: {ref_type}',
                'valid_types': ['payment', 'complaint', 'connection', 'ticket', 'outage', 'meter']
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception:
        return Response({
            'error': f'No {ref_type} found with reference {ref} for your account.'
        }, status=status.HTTP_404_NOT_FOUND)


# ══════════════════════════════════════════════════════════════════════════
# 3. CONSUMER DASHBOARD SUMMARY API
# Returns all data for a consumer in one call
# ══════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def consumer_summary(request):
    """
    GET /api/summary/

    Returns complete summary of logged-in consumer's data.
    A mobile app would call this once to populate its home screen.
    """

    user = request.user

    payments    = BillPayment.objects.filter(user=user).order_by('-created_at')[:5]
    complaints  = Complaint.objects.filter(user=user).order_by('-created_at')[:5]
    connections = ConnectionRequest.objects.filter(user=user).order_by('-created_at')[:3]
    outages     = PowerOutage.objects.filter(user=user).order_by('-created_at')[:5]
    readings    = MeterReading.objects.filter(user=user).order_by('-created_at')[:6]
    tickets     = SupportTicket.objects.filter(user=user).order_by('-created_at')[:5]

    # Last meter reading
    last_reading = readings.first()

    # Total units this month
    from django.utils import timezone
    now = timezone.now()
    monthly_readings = MeterReading.objects.filter(
        user=user,
        created_at__year=now.year,
        created_at__month=now.month
    )
    total_units_this_month = sum(
        float(r.units_consumed) for r in monthly_readings
    )

    # Pending payments count
    pending_payments = payments.filter(payment_status='pending').count()

    # Open complaints count
    open_complaints = Complaint.objects.filter(
        user=user, status__in=['registered', 'acknowledged', 'in_progress']
    ).count()

    return Response({
        'consumer': {
            'name'    : user.get_full_name() or user.username,
            'email'   : user.email,
            'username': user.username,
        },
        'summary': {
            'total_units_this_month': round(total_units_this_month, 2),
            'pending_payments'      : pending_payments,
            'open_complaints'       : open_complaints,
            'last_reading'          : {
                'reading_id'    : last_reading.reading_id if last_reading else None,
                'units_consumed': str(last_reading.units_consumed) if last_reading else None,
                'date'          : last_reading.reading_date if last_reading else None,
                'source'        : last_reading.source if last_reading else None,
                'auto_verified' : last_reading.auto_verified if last_reading else None,
            }
        },
        'recent': {
            'payments'    : BillPaymentSerializer(payments, many=True).data,
            'complaints'  : ComplaintSerializer(complaints, many=True).data,
            'connections' : ConnectionRequestSerializer(connections, many=True).data,
            'outages'     : PowerOutageSerializer(outages, many=True).data,
            'readings'    : MeterReadingSerializer(readings, many=True).data,
            'tickets'     : SupportTicketSerializer(tickets, many=True).data,
        }
    })


# ══════════════════════════════════════════════════════════════════════════
# 4. METER READINGS HISTORY API
# Get all meter readings for a consumer
# ══════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meter_readings_list(request):
    """
    GET /api/meter-readings/
    GET /api/meter-readings/?consumer=CON0000001
    GET /api/meter-readings/?source=smart_meter

    Returns list of meter readings for logged-in user.
    """

    readings = MeterReading.objects.filter(user=request.user).order_by('-created_at')

    # Filter by consumer number
    consumer = request.GET.get('consumer')
    if consumer:
        readings = readings.filter(consumer_number=consumer)

    # Filter by source
    source = request.GET.get('source')
    if source:
        readings = readings.filter(source=source)

    serializer = MeterReadingSerializer(readings, many=True)
    return Response({
        'count'  : readings.count(),
        'results': serializer.data
    })


# ══════════════════════════════════════════════════════════════════════════
# 5. API HEALTH CHECK
# Simple endpoint to test if API is working
# ══════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def api_health(request):
    """
    GET /api/health/

    Returns API status. Use this to test if everything is working.
    """
    return Response({
        'status' : 'online',
        'system' : 'PowerGrid REST API',
        'version': 'v1',
        'message': 'API is running. Smart meter integration ready.',
        'endpoints': {
            'health'         : 'GET  /api/health/',
            'submit_reading' : 'POST /api/meter-reading/submit/',
            'status_check'   : 'GET  /api/status/?type=payment&ref=PAY0000001',
            'summary'        : 'GET  /api/summary/',
            'meter_readings' : 'GET  /api/meter-readings/',
        }
    })


# ══════════════════════════════════════════════════════════════════════════
# 6. API DOCUMENTATION PAGE
# Human-readable docs at /api/docs/
# ══════════════════════════════════════════════════════════════════════════

from django.shortcuts import render

def api_docs(request):
    """
    GET /api/docs/
    Renders a human-readable API documentation page.
    """
    context = {
        'api_key': SMART_METER_API_KEY,
        'base_url': request.build_absolute_uri('/api/'),
    }
    return render(request, 'api/docs.html', context)
