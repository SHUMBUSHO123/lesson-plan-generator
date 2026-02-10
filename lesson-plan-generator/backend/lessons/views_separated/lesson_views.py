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

from lessons.models import UserProfile, Lesson, Unit, FREE_LESSON_LIMIT, SUBSCRIPTION_LIMITS
from lessons.utils.resolve_profile import resolve_profile


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
# Lesson Generation
# -----------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def generate_lesson_plan(request):
    profile = get_or_create_guest_profile(request)

    # Auto-expire subscription if needed
    profile.expire_subscription_if_needed()

    # Block inactive premium users
    if profile.is_premium and not profile.is_active:
        return Response(
            {"error": "Premium account inactive. Please contact admin."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Enforce lesson limit
    if not profile.can_generate_plan():
        return Response(
            {"redirect": "/payment/"},
            status=status.HTTP_403_FORBIDDEN
        )

    # Fetch Unit / Lesson safely
    unit_id = request.data.get("unit_id")
    lesson_id = request.data.get("lesson_id")
    unit = get_object_or_404(Unit, id=unit_id) if unit_id else None
    lesson = get_object_or_404(Lesson, id=lesson_id) if lesson_id else None

    # Prepare lesson info
    lesson_info = {
        "school_name": request.data.get("school_name") or profile.school_name or "",
        "teacher_name": request.data.get("teacher_name") or profile.teacher_name or "",
        "term": request.data.get("term") or profile.default_term or "",
        "class_size": request.data.get("class_size") or profile.class_size or 0,
        "references": lesson.references if lesson else profile.references or "",
        "lesson_title": lesson.title if lesson else "",
        "class_name": request.data.get("class") or "",
        "level": request.data.get("level") or "",
        "subject": request.data.get("subject") or (unit.subject.name if unit and unit.subject else ""),
        "date": request.data.get("date", "")
    }

    # Unit info
    unit_info = {
        "unit_number": getattr(unit, "number", 1) if unit else 1,
        "unit_title": unit.title if unit else "",
        "key_unit_competence": unit.key_unit_competence if unit else f"Understand {lesson_info['lesson_title']}",
        "total_lessons": unit.lessons.count() if unit and hasattr(unit, "lessons") else 1
    }

    # Lesson steps
    steps = []
    if lesson and hasattr(lesson, "lesson_steps"):
        for idx, step in enumerate(lesson.lesson_steps.all(), start=1):
            steps.append({
                "order": idx,
                "title": step.title or f"Step {idx}",
                "duration_minutes": step.duration_minutes or 5,
                "teacher_activity": step.teacher_activity or "",
                "learner_activity": step.learner_activity or ""
            })
    else:
        # Default steps for preview
        steps = [
            {"order": 1, "title": "Introduction", "duration_minutes": 10, "teacher_activity": "Introduce topic", "learner_activity": "Listen"},
            {"order": 2, "title": "Development", "duration_minutes": 25, "teacher_activity": "Explain concept", "learner_activity": "Practice"},
            {"order": 3, "title": "Conclusion", "duration_minutes": 5, "teacher_activity": "Summarize", "learner_activity": "Ask questions"},
        ]

    # Increment lesson usage
    try:
        profile.use_lesson()
    except Exception as e:
        return Response({"error": f"Failed to record lesson usage: {str(e)}"}, status=500)

    context = {
        "lesson_info": lesson_info,
        "unit_info": unit_info,
        "steps": steps,
        "lesson_number": request.data.get("lesson_no", 1),
        "lesson_duration": request.data.get("duration", 40),
        "special_needs": request.data.get("specialNeeds", "No specific needs identified")
    }

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
    return JsonResponse({"active": profile.is_subscription_active(), "expires_at": profile.subscription_expiry})


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
