from django.shortcuts import render, redirect
from django.http import FileResponse, Http404
from django.conf import settings
import os

def home(request):
    return render(request, 'home.html')



def service_worker(request):
    """Serve the service worker JS at /serviceworker.js"""
    sw_path = os.path.join(settings.BASE_DIR, 'static', '/serviceworker.js')
    if not os.path.exists(sw_path):
        raise Http404('Service worker not found')
    return FileResponse(open(sw_path, 'rb'), content_type='application/javascript')
