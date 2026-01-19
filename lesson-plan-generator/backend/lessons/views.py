# File: /lesson-plan-generator/backend/lessons/views.py

from datetime import timedelta
from django.shortcuts import render, redirect
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
import uuid
from django.views.decorators.csrf import csrf_exempt
import json

from .mtn_service import request_payment
from .models import Level, Class, Subject, Unit, Lesson, UserProfile, Subscription
from .serializers import LevelSerializer, ClassSerializer, SubjectSerializer, UnitSerializer, LessonSerializer

# -----------------------------
# Landing & Pricing
# -----------------------------
def landing(request):
    return render(request, 'landing.html')


def pricing(request):
    return render(request, 'pricing.html')


# -----------------------------
# Register / Login / Logout
# -----------------------------
@csrf_exempt
def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        device_id = request.POST.get("device_id") or str(uuid.uuid4())

        if User.objects.filter(username=email).exists():
            return JsonResponse({"error": "Email already registered"}, status=400)

        user = User.objects.create_user(username=email, email=email, password=password)
        profile = UserProfile.objects.create(user=user, device_id=device_id)

        login(request, user)
        return redirect("index")

    return render(request, "register.html")


@csrf_exempt
def login_user(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(username=email, password=password)
        if user:
            login(request, user)

            # Assign device_id if provided
            device_id = request.POST.get("device_id") or str(uuid.uuid4())
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.device_id = device_id
            profile.save()

            return redirect("index")

        return render(request, "login.html", {"error": "Invalid credentials"})

    return render(request, "login.html")


def logout_user(request):
    logout(request)
    return redirect("landing")


# -----------------------------
# Index with Hybrid Device + User
# -----------------------------
@never_cache
def index(request):
    device_id = request.GET.get('device_id') or str(uuid.uuid4())

    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.device_id = device_id
        profile.save()
    else:
        # Anonymous user → track by device
        anon_username = f"anon_{device_id}"
        anon_user, _ = User.objects.get_or_create(
            username=anon_username,
            defaults={'email': f'{device_id}@example.com', 'password': '!'}
        )
        profile, _ = UserProfile.objects.get_or_create(
            device_id=device_id,
            defaults={'user': anon_user}
        )

    return render(request, 'index.html', {'profile': profile})


# -----------------------------
# Payment Page
# -----------------------------
@never_cache
def payment_page(request):
    return render(request, 'payment.html')


# -----------------------------
# Increment Free Plan Usage (Hybrid)
# -----------------------------
@csrf_exempt
def increment_free_plan(request):
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        profile = UserProfile.objects.filter(device_id=device_id).first()
        if not profile:
            return JsonResponse({"error": "Profile not found"}, status=404)

        # Only increment if not premium
        if not profile.premium_active:
            profile.free_plans_used += 1
            profile.save()

        return JsonResponse({
            "free_plans_used": profile.free_plans_used,
            "premium_active": profile.premium_active
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# -----------------------------
# CRUD ViewSets
# -----------------------------
class LevelViewSet(viewsets.ModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer


class ClassViewSet(viewsets.ModelViewSet):
    serializer_class = ClassSerializer

    def get_queryset(self):
        qs = Class.objects.all()
        level_id = self.request.query_params.get('level_id')
        if level_id:
            qs = qs.filter(level_id=level_id)
        return qs


class SubjectViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectSerializer

    def get_queryset(self):
        qs = Subject.objects.all()
        class_id = self.request.query_params.get('class_id')
        if class_id:
            qs = qs.filter(class_field_id=class_id)
        return qs


class UnitViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSerializer

    def get_queryset(self):
        qs = Unit.objects.all()
        subject_id = self.request.query_params.get('subject_id')
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        return qs


class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer

    def get_queryset(self):
        qs = Lesson.objects.all()
        unit_id = self.request.query_params.get('unit_id')
        if unit_id:
            qs = qs.filter(unit_id=unit_id)
        return qs


# -----------------------------
# Generate Lesson Plan (Hybrid & Free/Premium)
# -----------------------------
@api_view(['POST'])
def generate_lesson_plan(request):
    device_id = request.data.get('device_id')
    if not device_id:
        return Response({"error": "device_id is required"}, status=400)

    profile, _ = UserProfile.objects.get_or_create(device_id=device_id)

    # Lock date if subscription expired / not allowed
    allow_date = profile.allow_future_dates or profile.premium_active
    if not allow_date:
        return Response({"error": "Your subscription does not allow future dates."}, status=403)

    if profile.can_generate_plan():
        profile.use_plan()
        lesson_plan_data = {
            "message": "Lesson plan generated successfully",
            "free_plans_used": profile.free_plans_used,
            "premium_active": profile.premium_active,
            "lesson_plan": {
                "title": "Sample Lesson Plan",
                "units": "Unit 1: Fractions",
                "lessons": [
                    "Lesson 1: Introduction",
                    "Lesson 2: Practice",
                    "Lesson 3: Simplify"
                ]
            }
        }
        return Response(lesson_plan_data)
    else:
        return Response({
            "error": "Free lesson plan limit reached. Please subscribe to access more."
        }, status=403)


# -----------------------------
# Subscription / Payment
# -----------------------------
@api_view(['POST'])
def confirm_payment(request):
    device_id = request.data.get('device_id')
    plan = request.data.get('plan')

    if not device_id or not plan:
        return JsonResponse({"status": "failed", "error": "device_id and plan are required"}, status=400)

    days_map = {'weekly': 7, 'monthly': 30, 'term': 90}
    days = days_map.get(plan)

    if not days:
        return JsonResponse({"status": "failed", "error": "Invalid plan"}, status=400)

    profile = UserProfile.objects.filter(device_id=device_id).first()
    if not profile:
        return JsonResponse({"status": "failed", "error": "UserProfile not found"}, status=404)

    # Create or extend Subscription
    Subscription.objects.create(
        user_profile=profile,
        plan=plan,
        end_date=timezone.now() + timedelta(days=days),
        active=True
    )

    profile.premium_active = True
    profile.allow_future_dates = True
    profile.save()

    return JsonResponse({"status": "success"})


@api_view(['GET'])
def check_subscription(request):
    device_id = request.GET.get('device_id')
    profile = UserProfile.objects.filter(device_id=device_id).first()

    if not profile:
        return JsonResponse({"active": False, "free_plans_used": 0})

    active = Subscription.objects.filter(
        user_profile=profile,
        active=True,
        end_date__gte=timezone.now()
    ).exists()

    return JsonResponse({
        "active": active,
        "free_plans_used": profile.free_plans_used
    })


@api_view(['POST'])
def initiate_mtn_payment(request):
    device_id = request.data.get('device_id')
    plan = request.data.get('plan')
    phone = request.data.get('phone')

    plan_prices = {'weekly': 20, 'monthly': 50, 'term': 111}

    if plan not in plan_prices:
        return Response({"error": "Invalid plan"}, status=400)

    amount = plan_prices[plan]

    try:
        ref_id = request_payment(amount=amount, phone=phone, external_id=device_id)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

    return Response({"status": "PENDING", "reference_id": ref_id})
