from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from django.http import FileResponse
from django.conf import settings
import os
from lessons.views import (
    index,
    LevelViewSet,
    ClassViewSet,
    SubjectViewSet,
    UnitViewSet,
    LessonViewSet,
    generate_lesson_plan,
    confirm_payment
)

router = routers.DefaultRouter()
router.register(r'levels', LevelViewSet, basename='level')
router.register(r'classes', ClassViewSet, basename='class')
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'units', UnitViewSet, basename='unit')
router.register(r'lessons', LessonViewSet, basename='lesson')
def service_worker(request):
    return FileResponse(
        open(os.path.join(settings.BASE_DIR, 'static', 'sw.js'), 'rb'),
        content_type='application/javascript'
    )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sw.js', service_worker),
    path('', index, name='index'),
    path('api/', include(router.urls)),
    path('api/generate/', generate_lesson_plan, name='generate_lesson_plan'),
    path('api/confirm-payment/', confirm_payment, name='confirm_payment'),
]
