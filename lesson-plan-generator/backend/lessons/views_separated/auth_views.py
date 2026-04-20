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
from lessons.models import (
    UserProfile, GeneratedLessonPlan,
    TopBanner, HeroBanner, BottomAd,          # ← HeroBanner added
)


# ─────────────────────────────────────────────────────────────
#  ADS HELPER  — call this in any view, pass the page flag
# ─────────────────────────────────────────────────────────────
def get_ads_context(page: str) -> dict:
    """
    Returns top_banners, hero_banners, bottom_ads filtered for `page`.

    Usage in any view:
        context.update(get_ads_context('landing'))   # landing page
        context.update(get_ads_context('index'))     # index/dashboard
        context.update(get_ads_context('pricing'))   # pricing page
    """
    flag = f'show_on_{page}'          # e.g. 'show_on_landing'
    return {
        'top_banners':  TopBanner.objects.filter(active=True,  **{flag: True}).order_by('order'),
        'hero_banners': HeroBanner.objects.filter(active=True, **{flag: True}).order_by('order'),
        'bottom_ads':   BottomAd.objects.filter(active=True,   **{flag: True}).order_by('order'),
    }


# -----------------------------
# Landing & Pricing
# -----------------------------
def landing(request):
    context = {}
    context.update(get_ads_context('landing'))
    return render(request, 'landing.html', context)


def pricing(request):
    plan = request.GET.get('plan', '')
    context = {'selected_plan': plan}
    context.update(get_ads_context('pricing'))
    return render(request, 'pricing.html', context)


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
    request.session.pop('device_id', None)
    logout(request)
    return redirect("landing")

from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model

User = get_user_model()

def password_reset_direct(request):
    error = None
    success = None

    if request.method == "POST":
        email        = request.POST.get("email", "").strip().lower()
        new_password = request.POST.get("new_password", "")
        confirm      = request.POST.get("confirm_password", "")

        if not email or not new_password or not confirm:
            error = "All fields are required."
        elif new_password != confirm:
            error = "Passwords do not match."
        elif len(new_password) < 6:
            error = "Password must be at least 6 characters."
        else:
            try:
                user = User.objects.get(email__iexact=email)
                user.set_password(new_password)
                user.save()
                return redirect("/api/login/?password_reset=1")
            except User.DoesNotExist:
                error = "No account found with that email address."

    return render(request, "password_reset_direct.html", {"error": error})


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

    context = {
        'profile':             profile,
        'dashboard_bootstrap': dashboard_bootstrap,
    }
    context.update(get_ads_context('index'))
    return render(request, 'index.html', context)