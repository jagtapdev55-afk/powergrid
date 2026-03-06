"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
 
from myapp.views import (
    home, send_email_view, user_dashboard,
    connection_request_view, bill_payment_view,
    complaint_registration_view, power_outage_report_view,
    meter_reading_submission_view, faq_view,
    support_ticket_view, my_applications_view,
    ticket_detail_view,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('captcha/', include('captcha.urls')),
    path('send-email/', send_email_view, name='send_email'), 
    path('', include('pwa.urls')),  # PWA URLs
    path('serviceworker.js', views.service_worker, name='serviceworker'),
    path('dashboard/', user_dashboard, name='user_dashboard'),
    
    path('services/connection-request/', connection_request_view, name='connection_request'),
    path('services/bill-payment/', bill_payment_view, name='bill_payment'),
    path('services/complaint/', complaint_registration_view, name='complaint_registration'),
    path('services/power-outage/', power_outage_report_view, name='power_outage_report'),
    path('services/meter-reading/', meter_reading_submission_view, name='meter_reading_submission'),
    path('services/faq/', faq_view, name='faq'),
    path('services/support/', support_ticket_view, name='support_ticket'),
    
    # My Applications
    path('my-applications/', my_applications_view, name='my_applications'),
    path('services/support/ticket/<int:ticket_id>/', ticket_detail_view, name='ticket_detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
#**What's happening?**
##- `path('dashboard/', ...)` = When user visits `/dashboard/`, call `user_dashboard` view
## `name='user_dashboard'` = We can use this name in templates like `{% url 'user_dashboard' %}


