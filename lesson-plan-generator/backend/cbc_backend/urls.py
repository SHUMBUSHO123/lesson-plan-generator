from django.contrib import admin
from django.urls import path, include
from django.http import FileResponse
from django.conf import settings
import os

from lessons.views import index

# Service worker route
def service_worker(request):
    return FileResponse(
        open(os.path.join(settings.BASE_DIR, 'static', 'sw.js'), 'rb'),
        content_type='application/javascript'
    )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sw.js', service_worker),
    path('', index, name='index'),          # Homepage
    path('api/', include('lessons.urls')),  # Include all lessons app API routes
]
