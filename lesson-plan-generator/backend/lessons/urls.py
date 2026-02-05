# lessons/urls.py

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

router = DefaultRouter()
router.register(r'levels', LevelViewSet, basename='level')
router.register(r'classes', ClassViewSet, basename='class')
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'units', UnitViewSet, basename='unit')
router.register(r'lessons', LessonViewSet, basename='lesson')

urlpatterns = [
    path("increment_free_plan/", views.increment_free_plan, name="increment_free_plan"),
    path("generate_lesson_plan/", generate_lesson_plan, name="generate_lesson_plan"),
    path("confirm-payment/", confirm_payment, name="confirm_payment"),
    path("check-subscription/", check_subscription, name="check_subscription"),
    path("initiate-mtn-payment/", initiate_mtn_payment, name="initiate_mtn_payment"),

    # pages
    path("index/", views.index, name="index"),
    path("register/", views.register, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("pricing/", views.pricing, name="pricing"),
    path("payment/", views.payment_page, name="payment"),
]

urlpatterns += router.urls
