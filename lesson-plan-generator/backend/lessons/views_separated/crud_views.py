from rest_framework import viewsets
from lessons.models import Level, Class, Subject, Unit, Lesson
# NEW (absolute import, always works)
from lessons.serializers import LevelSerializer, ClassSerializer, SubjectSerializer, UnitSerializer, LessonSerializer



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
