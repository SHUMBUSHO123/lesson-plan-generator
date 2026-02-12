# File: /lesson-plan-generator/backend/lessons/views_separated/lesson_views.py

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
from lessons.services.lesson_engine import build_strategy_steps  # ✅ NEW
import random


# -----------------------------
# Helpers
# -----------------------------
def get_or_create_guest_profile(request):
    """
    Ensure a profile exists for guest users based on device_id.
    """
    profile = resolve_profile(request)

    # Assign default lesson_limit for guests if unset
    if profile.is_guest and profile.lesson_limit is None:
        profile.lesson_limit = FREE_LESSON_LIMIT
        profile.save(update_fields=['lesson_limit'])

    return profile


# -----------------------------
# Lesson Generation (Refactored)
# -----------------------------
# -----------------------------
# Lesson Generation
# -----------------------------
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

 
 # your existing guest handling

@api_view(['POST'])
@permission_classes([AllowAny])
def generate_lesson_plan(request):
    """
    Generate a lesson plan HTML using build_lesson_plan_context helper.
    Handles free lesson limits, premium access, and dynamic steps.
    """
    # -----------------------------
    # Get user/guest profile
    # -----------------------------
    profile = get_or_create_guest_profile(request)
    profile.expire_subscription_if_needed()

    # Check premium account status
    if profile.is_premium and not profile.is_active:
        return Response({"error": "Premium account inactive. Please contact admin."}, status=403)

    # Check free lesson limits
    if not profile.can_generate_plan():
        return Response({"redirect": "/payment/"}, status=403)
    print("REQUEST.DATA:", request.data)

    # -----------------------------
    # Build context using helper
    # -----------------------------
    try:
        context = build_lesson_plan_context(request.data, profile)
    except PermissionError as e:
        return Response({"error": str(e), "redirect": "/payment/"}, status=403)
    except Exception as e:
        return Response({"error": f"Failed to build lesson plan context: {str(e)}"}, status=500)

    # -----------------------------
    # Record usage (already inside helper)
    # -----------------------------
    # Optional: profile.use_lesson() already handled if using prepare_lesson_plan_context

    # -----------------------------
    # Render HTML
    # -----------------------------
    html_content = render_to_string("partials/lesson_plan_table.html", context)
    return Response({"html": html_content})



# -----------------------------
# Access Check
# -----------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
def check_access(request):
    profile = get_or_create_guest_profile(request)
    profile.expire_subscription_if_needed()

    return Response({
        "can_generate": profile.is_active and profile.can_generate_plan(),
        "is_premium": profile.is_subscription_active(),
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

    profile.expire_subscription_if_needed()
    return JsonResponse({
        "active": profile.is_subscription_active(),
        "expires_at": profile.subscription_expiry
    })


# -----------------------------
# Prefill API
# -----------------------------
@api_view(['GET'])
def get_user_prefill(request):
    profile = get_or_create_guest_profile(request)
    return Response({
        "schoolName": profile.school_name or "",
        "teacherName": request.user.get_full_name() if request.user.is_authenticated else profile.teacher_name or "",
        "term": profile.default_term or "I",
        "classSize": profile.class_size or "",
        "references": profile.references or "",
        "unitTitle": "",
        "lessonTitle": ""
    })
