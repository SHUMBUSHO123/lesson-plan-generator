
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Level, Class, Subject, Unit, Lesson, DeviceAccess
from .serializers import LevelSerializer, ClassSerializer, SubjectSerializer, UnitSerializer, LessonSerializer
from django.utils import timezone

# -----------------------------
# Existing ViewSets for CRUD
# -----------------------------

class LevelViewSet(viewsets.ModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer

class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

# -----------------------------
# Device-based Lesson Plan APIs
# -----------------------------

@api_view(['POST'])
def generate_lesson_plan(request):
    """
    Generate a lesson plan for a device.
    New device: 3 free plans.
    After limit: prompt payment for 3 months premium.
    """
    device_id = request.data.get('device_id')
    if not device_id:
        return Response({"error": "device_id is required"}, status=400)

    device, created = DeviceAccess.objects.get_or_create(device_id=device_id)

    if device.can_generate_plan():
        device.use_plan()
        # Example: return dummy lesson plan data (replace with real generation logic)
        lesson_plan_data = {
            "message": "Lesson plan generated successfully",
            "free_plans_used": device.free_plans_used,
            "premium_active": device.premium_active,
            "lesson_plan": {
                "title": "Sample Lesson Plan",
                "units": "Unit 1: Fractions",
                "lessons": ["Lesson 1: Introduction", "Lesson 2: Practice", "Lesson 3: Simplify"]
            }
        }
        return Response(lesson_plan_data)
    else:
        return Response({
            "error": "Free lesson plan limit reached. Please pay 250 for 3 months premium access."
        }, status=403)

@api_view(['POST'])
def confirm_payment(request):
    """
    Confirm payment from device and activate premium for 90 days
    """
    device_id = request.data.get('device_id')
    payment_confirmed = request.data.get('payment_confirmed', False)

    if not device_id:
        return Response({"error": "device_id is required"}, status=400)

    device, created = DeviceAccess.objects.get_or_create(device_id=device_id)

    if payment_confirmed:
        device.activate_premium()
        return Response({"message": "Premium access activated for 90 days"})
    else:
        return Response({"error": "Payment not confirmed"}, status=400)
