
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from lessons.views import (
    LevelViewSet, ClassViewSet, SubjectViewSet,
    UnitViewSet, LessonViewSet,
    generate_lesson_plan, confirm_payment
)

# -----------------------------
# Default Router for CRUD APIs
# -----------------------------
router = DefaultRouter()
router.register(r'levels', LevelViewSet)
router.register(r'classes', ClassViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'units', UnitViewSet)
router.register(r'lessons', LessonViewSet)

# -----------------------------
# URL Patterns
# -----------------------------
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),  # CRUD endpoints
    path('api/generate-lesson/', generate_lesson_plan),  # Device-based lesson plan
    path('api/confirm-payment/', confirm_payment),      # Payment confirmation
]
