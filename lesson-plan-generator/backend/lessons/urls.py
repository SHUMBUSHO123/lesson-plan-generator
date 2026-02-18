from django.urls import path
from rest_framework.routers import DefaultRouter
from .views_separated import payment_views
from .views_separated.auth_views import register, login_user, logout_user
from .views_separated.crud_views import LevelViewSet, ClassViewSet, SubjectViewSet, UnitViewSet, LessonViewSet
from .views_separated.lesson_views import (
    generate_lesson_plan,
    check_access,
    get_user_prefill,
    get_user_dashboard,
    bulk_zip_download,
)
from .views import landing, pricing, get_logged_in_user_device_id, index

# Router
router = DefaultRouter()
router.register(r'levels', LevelViewSet, basename='level')
router.register(r'classes', ClassViewSet, basename='class')
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'units', UnitViewSet, basename='unit')
router.register(r'lessons', LessonViewSet, basename='lesson')

# URL patterns
urlpatterns = [
    # Pages
    path("", landing, name="landing"),
    path("index/", index, name="index"),
    path("register/", register, name="register"),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),
    path("pricing/", pricing, name="pricing"),
    path("payment/", payment_views.payment_page, name="payment"),

    # API endpoints
    path("get_logged_in_user_device_id/", get_logged_in_user_device_id, name="get_logged_in_user_device_id"),
    path("generate_lesson_plan/", generate_lesson_plan, name="generate_lesson_plan"),
    path("confirm-payment/", payment_views.confirm_payment, name="confirm_payment"),
    path("check-access/", check_access, name="check_access"),
    path("check-subscription/", payment_views.check_subscription, name="check_subscription"),
    path("subscription-success/", payment_views.subscription_success, name="subscription_success"),
    path("subscription-pending/", payment_views.subscription_pending, name="subscription_pending"),
    path('submit-payment-proof/', payment_views.submit_payment_proof, name='submit_payment_proof'),
    path("initiate-mtn-payment/", payment_views.initiate_mtn_payment, name="process_mtn_payment"),
    path("get_user_prefill/", get_user_prefill, name="get_user_prefill"),
    path("dashboard/", get_user_dashboard, name="user_dashboard"),
    path("plans/zip/", bulk_zip_download, name="bulk_zip_download"),
]

urlpatterns += router.urls