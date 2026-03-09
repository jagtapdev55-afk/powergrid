"""
api/urls.py
All REST API URL routes for PowerGrid.

Base URL: /api/

Endpoints:
    GET  /api/health/                          → API status check
    POST /api/meter-reading/submit/            → Smart meter / device submits reading
    GET  /api/meter-readings/                  → List meter readings (authenticated)
    GET  /api/status/?type=payment&ref=PAY001  → Check status of any application
    GET  /api/summary/                         → Full consumer dashboard summary
    GET  /api/docs/                            → API documentation page
"""

from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # ── Health Check ──────────────────────────────────────────────────────
    path('health/',                 views.api_health,            name='health'),

    # ── Smart Meter / Device Endpoint ─────────────────────────────────────
    path('meter-reading/submit/',   views.submit_meter_reading,  name='submit_meter_reading'),

    # ── Consumer Endpoints (require login) ────────────────────────────────
    path('meter-readings/',         views.meter_readings_list,   name='meter_readings_list'),
    path('status/',                 views.consumer_status,       name='consumer_status'),
    path('summary/',                views.consumer_summary,      name='consumer_summary'),

    # ── API Documentation ─────────────────────────────────────────────────
    path('docs/',                   views.api_docs,              name='api_docs'),
]
