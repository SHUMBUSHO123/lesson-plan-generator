print("🔥 lesson_views.py START LOADING")

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.template.loader import render_to_string
from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from lessons.helpers import build_lesson_plan_context, prepare_lesson_plan_context
from lessons.models import UserProfile, Lesson, Unit, FREE_LESSON_LIMIT, SUBSCRIPTION_LIMITS, TeachingStrategy, LessonStrategyStep
from lessons.utils.resolve_profile import resolve_profile
from lessons.models import TeachingStrategy
from lessons.services.lesson_engine import build_strategy_steps
import random
from django.db.models import F


def use_lesson_atomic(profile):
    """
    Increment lessons used safely using F() to avoid race conditions.
    """
    profile.lessons_used = F('lessons_used') + 1
    profile.save(update_fields=['lessons_used'])
    profile.refresh_from_db()


# -----------------------------
# Helpers
# -----------------------------
def get_or_create_guest_profile(request):
    """
    Ensure a profile exists for guest users based on device_id.
    """
    profile = resolve_profile(request)

    if profile.is_guest and profile.lesson_limit is None:
        profile.lesson_limit = FREE_LESSON_LIMIT
        profile.save(update_fields=['lesson_limit'])

    return profile


# -----------------------------
# Lesson Generation
# -----------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def generate_lesson_plan(request):
    """
    Generate a lesson plan HTML using build_lesson_plan_context helper.
    """
    profile = resolve_profile(request)
    profile.expire_subscription_if_needed()

    if profile.is_premium and not profile.is_active:
        return Response({"error": "Premium account inactive. Please contact admin."}, status=403)

    if not profile.can_generate_plan():
        return Response({"redirect": "/pricing/"}, status=403)

    print("REQUEST.DATA:", request.data)

    try:
        context = build_lesson_plan_context(request.data, profile)
    except PermissionError as e:
        return Response({"error": str(e), "redirect": "/pricing/"}, status=403)
    except Exception as e:
        return Response({"error": f"Failed to build lesson plan context: {str(e)}"}, status=500)

    try:
        use_lesson_atomic(profile)
        context['lesson_info']['lessons_used'] = profile.lessons_used
    except Exception as e:
        return Response({"error": f"Failed to record lesson usage: {str(e)}"}, status=500)

    try:
        html_content = render_to_string("partials/lesson_plan_table.html", context)
    except Exception as e:
        return Response({"error": f"Failed to render lesson plan: {str(e)}"}, status=500)

    return Response({"html": html_content})


# -----------------------------
# Access Check
# -----------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
def check_access(request):
    profile = get_or_create_guest_profile(request)

    # ✅ Only expire if subscription_expiry is explicitly SET and past
    # Do NOT expire admin-set is_premium=True with no expiry date
    if profile.subscription_expiry:
        profile.expire_subscription_if_needed()

    # ✅ is_premium=True set by admin ALWAYS grants premium access
    # even if subscription_plan or subscription_expiry are not set
    is_premium = profile.is_premium

    # ✅ can_generate: premium users always can, free users check limit
    can_generate = (
        profile.is_active and (
            is_premium or profile.can_generate_plan()
        )
    )

    return Response({
        "can_generate": can_generate,
        "is_premium": is_premium,
        "lessons_used": profile.lessons_used,
        "lesson_limit": profile.get_current_lesson_limit(),
        "is_active": profile.is_active,
        "message": "Access check complete"
    })


# -----------------------------
# Subscription Check
# -----------------------------
@api_view(['GET'])
def check_subscription(request):
    device_id = request.GET.get('device_id')
    if not device_id:
        return JsonResponse({"active": False, "expires_at": None})

    profile = UserProfile.objects.filter(device_id=device_id).first()
    if not profile:
        return JsonResponse({"active": False, "expires_at": None})

    # ✅ Same fix: only expire if expiry date is actually set
    if profile.subscription_expiry:
        profile.expire_subscription_if_needed()

    return JsonResponse({
        "active": profile.is_premium,  # ✅ Use is_premium directly
        "expires_at": profile.subscription_expiry
    })


# -----------------------------
# Prefill API
# -----------------------------
@api_view(['GET'])
def get_user_prefill(request):
    profile = get_or_create_guest_profile(request)

    unit_id = request.GET.get("unit_id")
    unit_display = ""
    lesson_title = ""

    if unit_id:
        unit = Unit.objects.filter(id=unit_id).first()
        if unit:
            unit_display = f"Unit {unit.number} – {unit.title}"
            first_lesson = unit.lessons.order_by("number").first()
            if first_lesson:
                lesson_title = first_lesson.title

    return Response({
        "schoolName": profile.school_name or "",
        "teacherName": request.user.get_full_name() if request.user.is_authenticated else profile.teacher_name or "",
        "term": profile.default_term or "I",
        "classSize": profile.class_size or "",
        "references": profile.references or "",
        "unitTitle": unit_display,
        "lessonTitle": lesson_title
    })
