# File: lessons/urls.py

from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views 
from .views import (
    LevelViewSet,
    ClassViewSet,
    SubjectViewSet,
    UnitViewSet,
    LessonViewSet,
    generate_lesson_plan,
    confirm_payment,
    check_subscription,
    initiate_mtn_payment
)

# Router for CRUD ViewSets
router = DefaultRouter()
router.register(r'levels', LevelViewSet, basename='level')
router.register(r'classes', ClassViewSet, basename='class')
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'units', UnitViewSet, basename='unit')
router.register(r'lessons', LessonViewSet, basename='lesson')

# API endpoints
urlpatterns = [
    path('generate/', generate_lesson_plan, name='generate_lesson_plan'),
    path('confirm-payment/', confirm_payment, name='confirm_payment'),
    path('check-subscription/', check_subscription, name='check_subscription'),
    path('initiate-mtn-payment/', initiate_mtn_payment, name='initiate_mtn_payment'),
    path('index/', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('pricing/', views.pricing, name='pricing'), 
    path('payment/', views.payment_page, name='payment'),
    path('api/initiate-mtn-payment/', views.initiate_mtn_payment, name='initiate_mtn_payment'),
    path('api/check-subscription/', views.check_subscription, name='check_subscription'),
]

# Include router URLs at the end
urlpatterns += router.urls
