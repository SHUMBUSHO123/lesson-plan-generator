from datetime import timedelta
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
import uuid
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from lessons.utils.resolve_profile import resolve_profile
from lessons.models import UserProfile
import json
from django.utils import timezone
from lessons.models import UserProfile, GeneratedLessonPlan



# -----------------------------
# Landing & Pricing
# -----------------------------
def landing(request):
    return render(request, 'landing.html')

def pricing(request):
    plan = request.GET.get('plan', '')
    return render(request, 'pricing.html', {'selected_plan': plan})


# ===============================
# DEVICE ID VIEW
# ===============================
@api_view(['GET'])
@permission_classes([AllowAny])
def get_logged_in_user_device_id(request):
    if not request.user.is_authenticated:
        return Response({"device_id": None}, status=200)
    profile = getattr(request.user, 'userprofile', None)
    return Response({"device_id": profile.device_id if profile else None}, status=200)


# -----------------------------
# Register
# -----------------------------
@csrf_exempt
def register(request):
    plan = request.GET.get('plan', '') or request.POST.get('plan', '')

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        incoming_device_id = request.POST.get("device_id")

        if User.objects.filter(username=email).exists():
            return render(request, "register.html", {
                "error": "Email already registered",
                "plan": plan
            })

        user = User.objects.create_user(username=email, email=email, password=password)
        profile = None

        if incoming_device_id:
            guest_profile = UserProfile.objects.filter(
                device_id=incoming_device_id, user__isnull=True
            ).first()
            if guest_profile:
                # ✅ Merge guest profile into the new user account
                # This preserves their lesson_used count from guest sessions
                guest_profile.user = user
                guest_profile.save()
                profile = guest_profile

        if not profile:
            profile = UserProfile.objects.create(
                user=user,
                device_id=incoming_device_id or str(uuid.uuid4())
            )

        login(request, user)
        request.session['device_id'] = profile.device_id

        if plan:
            return redirect(f"/payment/?plan={plan}")
        return redirect("index")

    return render(request, "register.html", {"plan": plan})


# -----------------------------
# Login
# -----------------------------
@csrf_exempt
def login_user(request):
    plan = request.GET.get('plan', '') or request.POST.get('plan', '')

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        incoming_device_id = request.POST.get("device_id")

        user = authenticate(username=email, password=password)
        if not user:
            return render(request, "login.html", {
                "error": "Invalid credentials",
                "plan": plan
            })

        login(request, user)
        profile, created = UserProfile.objects.get_or_create(user=user)

        if incoming_device_id:
            guest_profile = UserProfile.objects.filter(
                device_id=incoming_device_id, user__isnull=True
            ).first()
            if guest_profile:
                guest_profile.user = user
                guest_profile.save()
                profile = guest_profile

        if not profile.device_id:
            profile.device_id = incoming_device_id or str(uuid.uuid4())
            profile.save()

        request.session['device_id'] = profile.device_id

        if plan:
            return redirect(f"/payment/?plan={plan}")
        return redirect("index")

    return render(request, "login.html", {"plan": plan})


# -----------------------------
# Logout
# -----------------------------
def logout_user(request):
    # ✅ FIX 1: Clear device_id from session on logout
    # Without this, the next page load would resolve the
    # logged-out user's premium profile for the "guest"
    request.session.pop('device_id', None)
    logout(request)
    return redirect("landing")


# -----------------------------
# INDEX
# -----------------------------

@never_cache
def index(request):
    profile = None
    dashboard_bootstrap = None

    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if not profile.device_id:
            profile.device_id = str(uuid.uuid4())
            profile.save()

        profile.expire_subscription_if_needed()

        limit = profile.get_current_lesson_limit()
        used  = profile.lessons_used
        remaining = None if (profile.lesson_limit is None and profile.is_premium) else max(0, limit - used)

        plans = GeneratedLessonPlan.objects.filter(
            profile=profile
        ).order_by('-created_at')[:10]

        dashboard_bootstrap = json.dumps({
            "is_authenticated":    True,
            "is_premium":          profile.is_premium,
            "subscription_plan":   profile.subscription_plan,
            "subscription_expiry": profile.subscription_expiry.isoformat() if profile.subscription_expiry else None,
            "lessons_used":        used,
            "lesson_limit":        limit,
            "remaining":           remaining,
            "can_download_pdf":    profile.can_download_pdf,
            "can_download_docx":   profile.can_download_docx,
            "can_copy_word":       profile.can_copy_word,
            "recent_plans": [
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
            ],
        })
    # Guests: dashboard_bootstrap stays None — no fetch needed on load,
    # guest banner is handled lazily only when they generate a plan

    return render(request, 'index.html', {
        'profile':              profile,
        'dashboard_bootstrap':  dashboard_bootstrap,
    })