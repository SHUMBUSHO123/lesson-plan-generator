# lessons/views.py
"""
Stub to forward imports from refactored views_separated folder.
Keeps old imports (from lessons import views) working without changing URLs or templates.
"""
# lessons/views.py (stub)
from lessons.views_separated.auth_views import landing, pricing, register, login_user, logout_user, index,get_logged_in_user_device_id  # ✅ ADD THIS
from lessons.views_separated.crud_views import LevelViewSet, ClassViewSet, SubjectViewSet, UnitViewSet, LessonViewSet
from lessons.views_separated.lesson_views import (
    generate_lesson_plan,
    get_user_prefill,
    check_access,
    get_user_dashboard,
    bulk_zip_download,
)
from lessons.views_separated.payment_views import confirm_payment, check_subscription, initiate_mtn_payment, payment_page  # <- add this
from lessons.views_separated.bot_views import chat_bot_api, user_status_api  
