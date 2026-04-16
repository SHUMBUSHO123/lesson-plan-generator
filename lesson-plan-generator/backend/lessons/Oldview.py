

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
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
import json
from .mtn_service import request_payment
from .models import Level, Class, Subject, Unit, Lesson, UserProfile, Subscription
from .serializers import LevelSerializer, ClassSerializer, SubjectSerializer, UnitSerializer, LessonSerializer
from lessons.utils.resolve_profile import resolve_profile
from rest_framework.permissions import IsAuthenticated
from django.template.loader import render_to_string



# -----------------------------
# Landing & Pricing
# -----------------------------
def landing(request):
    return render(request, 'landing.html')

def pricing(request):
    return render(request, 'pricing.html')


# ===============================
# DEVICE ID VIEW
# ===============================
@api_view(['GET'])
@permission_classes([AllowAny])
def get_logged_in_user_device_id(request):
    profile = getattr(request.user, 'userprofile', None)
    if not request.user.is_authenticated:
        return Response({"device_id": None}, status=200)
      

# -----------------------------
# Register / Login / Logout
# -----------------------------
@csrf_exempt
def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        incoming_device_id = request.POST.get("device_id")  # optional from client

        # Check if user already exists
        if User.objects.filter(username=email).exists():
            return JsonResponse({"error": "Email already registered"}, status=400)

        # Create new user
        user = User.objects.create_user(username=email, email=email, password=password)

        profile = None

        if incoming_device_id:
            # Try to find a guest profile with this device_id
            guest_profile = UserProfile.objects.filter(device_id=incoming_device_id, user__isnull=True).first()
            if guest_profile:
                # Merge guest profile into new user
                guest_profile.user = user
                guest_profile.save()  # write-once device_id ensures safety
                profile = guest_profile

        # If no guest profile exists, create a new profile
        if not profile:
            profile = UserProfile.objects.create(
                user=user,
                device_id=incoming_device_id or str(uuid.uuid4())
            )

        # Log the user in
        login(request, user)

        # Store device_id in session for frontend usage
        request.session['device_id'] = profile.device_id

        return redirect("index")

    # GET request renders registration page
    return render(request, "register.html")


@csrf_exempt
def login_user(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        incoming_device_id = request.POST.get("device_id")  # optional from client

        # Authenticate user
        user = authenticate(username=email, password=password)
        if not user:
            return render(request, "login.html", {"error": "Invalid credentials"})

        # Log the user in
        login(request, user)

        # Get or create the UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)

        # Merge with guest profile if exists (device-only)
        if incoming_device_id:
            guest_profile = UserProfile.objects.filter(device_id=incoming_device_id, user__isnull=True).first()
            if guest_profile:
                guest_profile.user = user
                guest_profile.save()
                profile = guest_profile  # use merged profile

        # Ensure device_id is set (write-once enforced by model)
        if not profile.device_id:
            profile.device_id = incoming_device_id or str(uuid.uuid4())
            profile.save()

        # Store device_id in session for frontend
        request.session['device_id'] = profile.device_id

        return redirect("index")

    # GET request renders login page
    return render(request, "login.html")


def logout_user(request):
    logout(request)
    return redirect("landing")

# -----------------------------
# INDEX WITH HYBRID DEVICE + USER
# -----------------------------
@never_cache
def index(request):
    if request.user.is_authenticated:
        # Get or create profile for logged-in user
        profile, created = UserProfile.objects.get_or_create(user=request.user)

        # Assign a new device_id only if none exists
        if not profile.device_id:
            profile.device_id = str(uuid.uuid4())
            profile.save()

    else:
        # Anonymous / guest user
        device_id = request.GET.get('device_id') or str(uuid.uuid4())
        profile, _ = UserProfile.objects.get_or_create(
            device_id=device_id,
            defaults={'user': None}  # Explicitly set no user
        )

    return render(request, 'index.html', {'profile': profile})

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


from django.shortcuts import render

def payment_page(request):
    """
    Render the payment page.
    """
    return render(request, "payment.html")  # make sure you have templates/payment.html

# -----------------------------
# Lesson Generation
# -----------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def generate_lesson_plan(request):
    # 🔐 Canonical identity resolution (guest or logged-in)
    profile = resolve_profile(request)

    # Refresh subscription (expire old premium if needed)
    profile.expire_subscription_if_needed()

    # FINAL access gate (active + lesson limit)
    if not profile.is_active or not profile.can_generate_plan():
        return Response(
            {"error": "Lesson plan limit reached. Please subscribe."},
            status=403
        )

    # Load Unit and Lesson objects
    unit_id = request.data.get("unit_id")
    lesson_id = request.data.get("lesson_id")

    unit = Unit.objects.filter(id=unit_id).first()
    lesson = Lesson.objects.filter(id=lesson_id).first()

    # Prepare lesson info (request → profile → fallback)
    lesson_info = {
        "school_name": request.data.get("school_name") or profile.school_name or "",
        "teacher_name": request.data.get("teacher_name") or profile.teacher_name or "",
        "term": request.data.get("term") or profile.default_term or "",
        "class_size": request.data.get("class_size") or profile.class_size or 0,
        "references": (
            lesson.references if lesson
            else profile.references or ""
        ),
        "lesson_title": lesson.title if lesson else "",
        "class_name": request.data.get("class") or "",
        "level": request.data.get("level") or "",
        "subject": (
            request.data.get("subject")
            or (unit.subject.name if unit and unit.subject else "")
        ),
        "date": request.data.get("date", "")
    }

    # Prepare unit info
    unit_info = {
        "unit_number": getattr(unit, "number", 1) if unit else 1,
        "unit_title": unit.title if unit else "",
        "key_unit_competence": (
            unit.key_unit_competence
            if unit else f"Understand {lesson_info['lesson_title']}"
        ),
        "total_lessons": (
            unit.lessons.count()
            if unit and hasattr(unit, "lessons") else 1
        )
    }

    # Prepare lesson steps
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
        # Default fallback steps
        steps = [
            {
                "order": 1,
                "title": "Introduction",
                "duration_minutes": 10,
                "teacher_activity": "Introduce topic",
                "learner_activity": "Listen"
            },
            {
                "order": 2,
                "title": "Development",
                "duration_minutes": 25,
                "teacher_activity": "Explain concept",
                "learner_activity": "Practice"
            },
            {
                "order": 3,
                "title": "Conclusion",
                "duration_minutes": 5,
                "teacher_activity": "Summarize",
                "learner_activity": "Ask questions"
            }
        ]

    # ✅ Register lesson usage (atomic, tied to profile)
    profile.use_lesson()

    # Render HTML response
    context = {
        "lesson_info": lesson_info,
        "unit_info": unit_info,
        "steps": steps,
        "lesson_number": request.data.get("lesson_no", 1),
        "lesson_duration": request.data.get("duration", 40),
        "special_needs": request.data.get(
            "specialNeeds",
            "No specific needs identified"
        )
    }

    html_content = render_to_string(
        "partials/lesson_plan_table.html",
        context
    )

    return Response({"html": html_content})

# -----------------------------
# Confirm Payment / Activate Premium
# -----------------------------
@api_view(['POST'])
def confirm_payment(request):
    # 🔐 Canonical identity resolution
    profile = resolve_profile(request)

    plan = request.data.get("plan")

    # Validate input
    if not plan:
        return JsonResponse(
            {"status": "failed", "error": "plan is required"},
            status=400
        )

    # Map plan to duration in days
    plan_days_map = {
        "weekly": 7,
        "monthly": 30,
        "term": 90
    }

    days = plan_days_map.get(plan)
    if not days:
        return JsonResponse(
            {"status": "failed", "error": "Invalid plan"},
            status=400
        )

    # Activate premium safely
    profile.activate_premium(plan=plan, days=days, reset_usage=True)

    return JsonResponse({
        "status": "success",
        "message": f"Subscription '{plan}' activated for {days} days.",
        "subscription_expiry": profile.subscription_expiry
    })
# -----------------------------
# Access Check
# -----------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
def check_access(request):
    # 🔐 Single authoritative identity resolution
    profile = resolve_profile(request)

    # Refresh subscription safely (no matter guest or logged-in)
    profile.expire_subscription_if_needed()

    return Response({
        "can_generate": profile.is_active and profile.can_generate_plan(),
        "is_premium": profile.is_subscription_active(),
        "lessons_used": profile.lessons_used,
        "lesson_limit": profile.lesson_limit,
        "is_active": profile.is_active,
        "message": "Access check complete"
    })

@api_view(['GET'])
def check_subscription(request):
    device_id = request.GET.get('device_id')

    if not device_id:
        return JsonResponse({"active": False, "expires_at": None})

    profile = UserProfile.objects.filter(device_id=device_id).first()
    if not profile:
        return JsonResponse({"active": False, "expires_at": None})

    # Refresh subscription
    profile.expire_subscription_if_needed()

    return JsonResponse({
        "active": profile.is_subscription_active(),
        "expires_at": profile.subscription_expiry
    })


@api_view(['GET'])
def get_user_prefill(request):
    # 🔐 Canonical identity resolution
    profile = resolve_profile(request)

    return Response({
        "schoolName": profile.school_name or "",
        "teacherName": (
            request.user.get_full_name()
            if request.user.is_authenticated
            else profile.teacher_name or ""
        ),
        "term": profile.default_term or "I",
        "classSize": profile.class_size or "",
        "references": profile.references or "",
        "unitTitle": "",
        "lessonTitle": ""
    })


@api_view(['POST'])
def initiate_mtn_payment(request):
    # 🔐 Canonical identity resolution
    profile = resolve_profile(request)

    plan = request.data.get("plan")
    phone = request.data.get("phone")

    # Validate input
    if not plan or not phone:
        return Response(
            {"error": "plan and phone are required"},
            status=400
        )

    # Pricing map (authoritative server-side)
    plan_prices = {
        "weekly": 20,
        "monthly": 50,
        "term": 111
    }

    if plan not in plan_prices:
        return Response({"error": "Invalid plan"}, status=400)

    amount = plan_prices[plan]

    try:
        # 🔐 External ID MUST be tied to canonical profile
        ref_id = request_payment(
            amount=amount,
            phone=phone,
            external_id=str(profile.id)  # ← NEVER device_id
        )
    except Exception as e:
        return Response(
            {"error": f"Payment initiation failed: {str(e)}"},
            status=500
        )

    return Response({
        "status": "PENDING",
        "reference_id": ref_id,
        "amount": amount,
        "plan": plan
    })