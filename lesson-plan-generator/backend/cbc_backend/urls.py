from django.contrib import admin
from django.urls import path, include
from django.http import FileResponse
from django.conf import settings
from django.conf.urls.static import static
import os
from lessons import views
from lessons.views_separated.payment_views import payment_page


def service_worker(request):
    return FileResponse(
        open(os.path.join(settings.BASE_DIR, 'static', 'sw.js'), 'rb'),
        content_type='application/javascript'
    )


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landing, name='landing'),
    path('index/', views.index, name='index'),
    path('pricing/', views.pricing, name='pricing'),
    path('payment/', payment_page, name='payment'),
    path('sw.js', service_worker),
    path('api/', include('lessons.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)