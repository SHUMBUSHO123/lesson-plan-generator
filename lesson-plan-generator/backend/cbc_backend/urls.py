# File: /lesson-plan-generator/backend/cbc_backend/urls.py

from django.contrib import admin
from django.urls import path, include
from django.http import FileResponse
from django.conf import settings
import os

from lessons import views
from lessons.views_separated.payment_views import payment_page

# Service worker route
def service_worker(request):
    return FileResponse(
        open(os.path.join(settings.BASE_DIR, 'static', 'sw.js'), 'rb'),
        content_type='application/javascript'
    )

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Page routes (root-level)
    path('', views.landing, name='landing'),      # Landing page at /
    path('index/', views.index, name='index'),    # Index page at /index/
    path('pricing/', views.pricing, name='pricing'),  # Pricing page at /pricing/
    path('payment/', payment_page, name='payment'),   # Payment page at /payment/

    # Service worker
    path('sw.js', service_worker),

    # API routes (all /api/... calls)
    path('api/', include('lessons.urls')),
]
