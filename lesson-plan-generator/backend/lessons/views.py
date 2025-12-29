# File: /lesson-plan-generator/backend/lessons/views.py

from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .mtn_service import request_payment


from .models import (
    Level, Class as ClassModel, Subject, Unit, Lesson,
    DeviceAccess, Subscription
)
from .serializers import (
    LevelSerializer, ClassSerializer,
    SubjectSerializer, UnitSerializer, LessonSerializer
)


# -----------------------------
# Index view
# -----------------------------
def index(request):
    return render(request, 'index.html')


# -----------------------------
# CRUD ViewSets with filtering
# -----------------------------
class LevelViewSet(viewsets.ModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer


class ClassViewSet(viewsets.ModelViewSet):
    serializer_class = ClassSerializer

    def get_queryset(self):
        qs = ClassModel.objects.all()
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
# Device-based Lesson Plan API
# -----------------------------
@api_view(['POST'])
def generate_lesson_plan(request):
    """
    Allows generating lesson plan for free plan devices or premium users.
    """
    device_id = request.data.get('device_id')
    if not device_id:
        return Response({"error": "device_id is required"}, status=400)

    device, _ = DeviceAccess.objects.get_or_create(device_id=device_id)

    if device.can_generate_plan():
        device.use_plan()
        lesson_plan_data = {
            "message": "Lesson plan generated successfully",
            "free_plans_used": device.free_plans_used,
            "premium_active": device.premium_active,
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
# Payment & Subscription
# -----------------------------
@api_view(['POST'])
def confirm_payment(request):
    """
    Confirm payment and activate subscription for device_id
    """
    device_id = request.data.get('device_id')
    plan = request.data.get('plan')

    if not device_id or not plan:
        return JsonResponse({"status": "failed", "error": "device_id and plan are required"}, status=400)

    days_map = {'weekly': 7, 'monthly': 30, 'term': 90}
    days = days_map.get(plan)

    if not days:
        return JsonResponse({"status": "failed", "error": "Invalid plan"}, status=400)

    # Create Subscription
    Subscription.objects.create(
        device_id=device_id,
        plan=plan,
        end_date=datetime.now() + timedelta(days=days),
        active=True
    )

    return JsonResponse({"status": "success"})


@api_view(['GET'])
def check_subscription(request):
    """
    Check if the device has an active subscription
    """
    device_id = request.GET.get('device_id')

    active = Subscription.objects.filter(
        device_id=device_id,
        active=True,
        end_date__gte=datetime.now()
    ).exists()

    return JsonResponse({"active": active})

@api_view(['POST'])
def initiate_mtn_payment(request):
    device_id = request.data.get('device_id')
    plan = request.data.get('plan')
    phone = request.data.get('phone')

    plan_prices = {
        'weekly': 20,
        'monthly': 50,
        'term': 111
    }

    if plan not in plan_prices:
        return Response({"error": "Invalid plan"}, status=400)

    amount = plan_prices[plan]

    try:
        ref_id = request_payment(
            amount=amount,
            phone=phone,
            external_id=device_id
        )
    except Exception as e:
        return Response({"error": str(e)}, status=500)

    return Response({
        "status": "PENDING",
        "reference_id": ref_id
    })
