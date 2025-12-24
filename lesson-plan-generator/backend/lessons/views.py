from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Level, Class as ClassModel, Subject, Unit, Lesson, DeviceAccess
from .serializers import LevelSerializer, ClassSerializer, SubjectSerializer, UnitSerializer, LessonSerializer
from django.shortcuts import render

# -----------------------------
# Index view
# -----------------------------
def index(request):
    return render(request, 'index.html')


# -----------------------------
# ViewSets for CRUD with filtering
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
# Device-based Lesson Plan APIs
# -----------------------------
@api_view(['POST'])
def generate_lesson_plan(request):
    device_id = request.data.get('device_id')
    if not device_id:
        return Response({"error": "device_id is required"}, status=400)

    device, created = DeviceAccess.objects.get_or_create(device_id=device_id)

    if device.can_generate_plan():
        device.use_plan()
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
