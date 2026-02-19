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
from lessons.models import (
    UserProfile, Lesson, Unit, FREE_LESSON_LIMIT, SUBSCRIPTION_LIMITS,
    TeachingStrategy, LessonStrategyStep, GeneratedLessonPlan
)
from lessons.utils.resolve_profile import resolve_profile
from lessons.services.lesson_engine import build_strategy_steps
import random
from django.db.models import F
import zipfile
import io
from django.http import HttpResponse


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

    # ── Persist plan for logged-in users only ─────────────────────────
    if request.user.is_authenticated:
        try:
            lesson_info = context.get('lesson_info', {})
            GeneratedLessonPlan.objects.create(
                profile       = profile,
                subject       = lesson_info.get('subject', request.data.get('subject', '')),
                unit_title    = lesson_info.get('unit_title', ''),
                lesson_title  = lesson_info.get('lesson_title', '')[:300],
                class_name    = lesson_info.get('class_name', request.data.get('class', '')),
                term          = request.data.get('term', ''),
                html_snapshot = html_content,
            )
        except Exception as save_err:
            print(f"⚠️  Could not save GeneratedLessonPlan: {save_err}")

    return Response({"html": html_content})


# -----------------------------
# Access Check
# -----------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
def check_access(request):
    profile = get_or_create_guest_profile(request)

    # ✅ Only expire if subscription_expiry is explicitly SET and past
    if profile.subscription_expiry:
        profile.expire_subscription_if_needed()

    is_premium = profile.is_premium

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

    if profile.subscription_expiry:
        profile.expire_subscription_if_needed()

    return JsonResponse({
        "active": profile.is_premium,
        "expires_at": profile.subscription_expiry
    })


# -----------------------------
# User Dashboard
# -----------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_dashboard(request):
    """
    Returns usage stats + last 10 generated lesson plans for the dashboard panel.
    Uses request.user.is_authenticated as the ONLY authority for auth state.
    Guests receive a counter only — no plan history, no premium data leakage.
    """
    is_authenticated = request.user.is_authenticated

    if is_authenticated:
        # Logged-in: get their real profile
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.expire_subscription_if_needed()

        limit = profile.get_current_lesson_limit()
        used  = profile.lessons_used

        # None only when lesson_limit is truly NULL (permanent admin grant)
        if profile.lesson_limit is None and profile.is_premium:
            remaining = None
        else:
            remaining = max(0, limit - used)

        payload = {
            "is_authenticated":    True,
            "is_premium":          profile.is_premium,
            "subscription_plan":   profile.subscription_plan,
            "subscription_expiry": (
                profile.subscription_expiry.isoformat()
                if profile.subscription_expiry else None
            ),
            "lessons_used":      used,
            "lesson_limit":      limit,
            "remaining":         remaining,
            "can_download_pdf":  profile.can_download_pdf,
            "can_download_docx": profile.can_download_docx,
            "can_copy_word":     profile.can_copy_word,
            "recent_plans":      [],
        }

        # Recent plans — only for logged-in users
        plans = GeneratedLessonPlan.objects.filter(
            profile=profile
        ).order_by('-created_at')[:10]

        payload["recent_plans"] = [
            {
                "id":           p.id,
                "subject":      p.subject,
                "unit_title":   p.unit_title,
                "lesson_title": p.lesson_title,
                "class_name":   p.class_name,
                "term":         p.term,
                "created_at":   p.created_at.strftime("%d %b %Y, %H:%M"),
            }
            for p in plans
        ]

    else:
        # Guest: resolve device-based profile for usage counter only
        profile = resolve_profile(request)

        limit     = profile.get_current_lesson_limit()
        used      = profile.lessons_used
        remaining = max(0, limit - used)

        payload = {
            "is_authenticated":    False,
            "is_premium":          False,
            "subscription_plan":   None,
            "subscription_expiry": None,
            "lessons_used":        used,
            "lesson_limit":        limit,
            "remaining":           remaining,
            "can_download_pdf":    False,
            "can_download_docx":   False,
            "can_copy_word":       False,
            "recent_plans":        [],
        }

    return Response(payload)


# -----------------------------
# Bulk ZIP Download
# -----------------------------
@api_view(['POST'])
def bulk_zip_download(request):
    """
    Accepts: { "plan_ids": [1, 2, 3] }
    Returns a ZIP of HTML snapshots.
    Security: only the owner's plans are included.
    """
    if not request.user.is_authenticated:
        return Response({"error": "Login required to download plans."}, status=401)

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    plan_ids = request.data.get('plan_ids', [])
    if not plan_ids or not isinstance(plan_ids, list):
        return Response({"error": "Provide a list of plan_ids."}, status=400)

    plans = GeneratedLessonPlan.objects.filter(
        id__in=plan_ids,
        profile=profile
    )

    if not plans.exists():
        return Response({"error": "No matching plans found."}, status=404)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for plan in plans:
            full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{plan.subject} – {plan.lesson_title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; font-size: 12pt; padding: 20px; color: #000; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 16pt; }}
    td, th {{ border: 1px solid #333; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f0f0f0; font-weight: bold; }}
  </style>
</head>
<body>
{plan.html_snapshot}
</body>
</html>"""
            safe_subject = "".join(
                c for c in plan.subject if c.isalnum() or c in " _-"
            )[:30].strip()
            safe_lesson = "".join(
                c for c in plan.lesson_title if c.isalnum() or c in " _-"
            )[:40].strip()
            date_str = plan.created_at.strftime("%Y%m%d")
            filename = f"{date_str}_{safe_subject}_{safe_lesson}.html".replace(" ", "_")
            zf.writestr(filename, full_html)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="CBC_Lesson_Plans.zip"'
    return response


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
        "schoolName":  profile.school_name or "",
        "teacherName": request.user.get_full_name() if request.user.is_authenticated else profile.teacher_name or "",
        "term":        profile.default_term or "I",
        "classSize":   profile.class_size or "",
        "references":  profile.references or "",
        "unitTitle":   unit_display,
        "lessonTitle": lesson_title
    })