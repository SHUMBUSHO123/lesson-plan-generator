from django.contrib import admin
from django.urls import path, include
from django.http import FileResponse
from django.conf import settings
from django.conf.urls.static import static
import os

def service_worker(request):
    return FileResponse(
        open(os.path.join(settings.BASE_DIR, 'static', 'sw.js'), 'rb'),
        content_type='application/javascript'
    )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sw.js', service_worker),
    path('api/', include('lessons.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)