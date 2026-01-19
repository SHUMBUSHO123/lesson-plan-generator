from django.contrib import admin
from django.urls import path, include
from django.http import FileResponse
from django.conf import settings
import os
from lessons import views

# Service worker route
def service_worker(request):
    return FileResponse(
        open(os.path.join(settings.BASE_DIR, 'static', 'sw.js'), 'rb'),
        content_type='application/javascript'
    )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landing, name='landing'),      # Landing page at /
    path('index/', views.index, name='index'),    # Index page at /index/
    path('sw.js', service_worker),
    path('api/', include('lessons.urls')),        # API routes
]
