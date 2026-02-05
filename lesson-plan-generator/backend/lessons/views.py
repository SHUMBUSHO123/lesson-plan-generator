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
from rest_framework.decorators import api_view

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
# -----------------------------
# Increment Free Plan Usage (Hybrid)
# -----------------------------
@csrf_exempt
def increment_free_plan(request):
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        if not device_id:
            return JsonResponse({"error": "Missing device_id"}, status=400)

        # Get or create UserProfile for this device
        profile, created = UserProfile.objects.get_or_create(device_id=device_id)

        # Only increment if not premium
        profile.check_subscription_status()  # auto-updates premium status if expired
        if not profile.is_premium:
            profile.free_plans_used += 1
            profile.save()

        return JsonResponse({
            "free_plans_used": profile.free_plans_used,
            "premium_active": profile.is_premium
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


@api_view(['POST'])
def generate_lesson_plan(request):
    from django.template.loader import render_to_string
    from django.utils.html import escape

    # -----------------------------
    # Validate device_id
    # -----------------------------
    device_id = request.data.get('device_id')
    if not device_id:
        return Response({"error": "device_id is required"}, status=400)

    # -----------------------------
    # Get or create UserProfile
    # -----------------------------
    profile, _ = UserProfile.objects.get_or_create(device_id=device_id)

    # -----------------------------
    # Check subscription / future date permission
    # -----------------------------
    allow_date = True
    # if not allow_date:
    #    return Response({"error": "Your subscription does not allow future dates."}, status=403)

    # -----------------------------
    # Check plan availability
    # -----------------------------
    if not profile.can_generate_plan():
        return Response({"error": "Free lesson plan limit reached. Please subscribe to access more."}, status=403)

    # -----------------------------
    # Track plan usage
    # -----------------------------
    profile.use_lesson()

    # -----------------------------
    # Fetch Unit and Lesson
    # -----------------------------
    unit_id = request.data.get("unit_id")
    lesson_id = request.data.get("lesson_id")

    unit = Unit.objects.filter(id=unit_id).first()
    lesson = Lesson.objects.filter(id=lesson_id).first()

    # -----------------------------
    # Build lesson_info and unit_info
    # -----------------------------
    lesson_info = {
        "school_name": request.data.get("school_name") or profile.school_name or "",
        "teacher_name": request.data.get("teacher_name") or profile.teacher_name or "",
        "term": request.data.get("term") or profile.default_term or "",
        "class_size": request.data.get("class_size") or profile.class_size or 0,
        "references": lesson.references if lesson else profile.references or "",
        "lesson_title": lesson.title if lesson else "",
        "class_name": request.data.get("class") or "",
        "level": request.data.get("level") or "",
        "subject": request.data.get("subject") or (unit.subject.title if unit and unit.subject else ""),
        "date": request.data.get('date','')
    }

    unit_info = {
        "unit_number": getattr(unit, "number", 1) if unit else 1,
        "unit_title": unit.title if unit else "",
        "key_unit_competence": unit.key_unit_competence if unit else f"Be able to understand and apply {lesson_info['lesson_title']} concepts",
        "total_lessons": unit.lessons.count() if unit and hasattr(unit, "lessons") else 1
    }

    # -----------------------------
    # Lesson steps
    # -----------------------------
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
        steps = [
            {"order": 1, "title": "Introduction", "duration_minutes": 10, "teacher_activity": "Introduce topic", "learner_activity": "Listen and respond"},
            {"order": 2, "title": "Development", "duration_minutes": 25, "teacher_activity": "Explain concept", "learner_activity": "Practice exercises"},
            {"order": 3, "title": "Conclusion", "duration_minutes": 5, "teacher_activity": "Summarize", "learner_activity": "Ask questions"}
        ]

    # -----------------------------
    # Prepare context for template
    # -----------------------------
    context = {
        'lesson_info': lesson_info,
        'unit_info': unit_info,
        'steps': steps,
        'lesson_number': request.data.get('lesson_no', 1),
        'lesson_duration': request.data.get('duration', 40),
        'special_needs': request.data.get('specialNeeds', 'No specific special educational needs identified in this class')
    }

    # -----------------------------
    # Render HTML from template
    # -----------------------------
    html_content = render_to_string('partials/lesson_plan_table.html', context)

    return Response({"html": html_content})



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

    profile.check_subscription_status()

    return JsonResponse({
        "active": profile.premium_active,
        "free_plans_used": profile.free_plans_used
    })


# -----------------------------
# Prefill User Data API
# -----------------------------
@api_view(['GET'])
def get_user_prefill(request):
    """
    Returns prefill data for logged-in user or by device_id
    """
    if request.user.is_authenticated:
        profile = UserProfile.objects.filter(user=request.user).first()
    else:
        device_id = request.GET.get('device_id')
        profile = UserProfile.objects.filter(device_id=device_id).first()

    if not profile:
        return Response({"error": "UserProfile not found"}, status=404)

    # Example: default or saved values
    prefill_data = {
        "schoolName": profile.school_name or "",
        "teacherName": (
            request.user.get_full_name()
            if request.user.is_authenticated and request.user.get_full_name()
            else profile.teacher_name or ""
    ),
        "term": profile.default_term or "I",
        "classSize": profile.class_size or "",
        "references": profile.references or "",
        "unitTitle": "",  # will be filled once teacher selects a unit
        "lessonTitle": "" # same
    }

    return Response(prefill_data)



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
