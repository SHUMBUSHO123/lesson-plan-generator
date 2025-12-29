from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    index,
    LevelViewSet,
    ClassViewSet,
    SubjectViewSet,
    UnitViewSet,
    LessonViewSet,
    generate_lesson_plan,
    confirm_payment,
    initiate_mtn_payment
)

# -----------------------------
# Router for CRUD endpoints
# -----------------------------
router = DefaultRouter()
router.register(r'levels', LevelViewSet, basename='level')
router.register(r'classes', ClassViewSet, basename='class')
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'units', UnitViewSet, basename='unit')
router.register(r'lessons', LessonViewSet, basename='lesson')

# -----------------------------
# URL Patterns
# -----------------------------
urlpatterns = [
    path('', index, name='index'),  # Homepage
    path('api/generate/', generate_lesson_plan, name='generate_lesson_plan'),
    path('api/confirm-payment/', confirm_payment, name='confirm_payment'),
    path('api/', include(router.urls)),  # Include all CRUD API routes
]
