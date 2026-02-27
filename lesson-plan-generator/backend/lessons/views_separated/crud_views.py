# File: /lesson-plan-generator/backend/lessons/views.py

from rest_framework import viewsets
from lessons.models import Level, Class, Subject, Unit, Lesson
from lessons.serializers import (
    LevelSerializer, ClassSerializer, SubjectSerializer,
    UnitSerializer, LessonSerializer
)

VALID_LANGUAGES = {'en', 'rw', 'sw', 'fr'}


def _get_lang(request):
    """
    Read ?lang= from query params.
    Defaults to 'en' if missing or invalid.
    """
    lang = request.query_params.get('lang', 'en')
    return lang if lang in VALID_LANGUAGES else 'en'


class LevelViewSet(viewsets.ModelViewSet):
    serializer_class = LevelSerializer

    def get_queryset(self):
        lang = _get_lang(self.request)
        return Level.objects.filter(language=lang, is_active=True)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['language'] = _get_lang(self.request)  # passed down to nested serializers
        return context


class ClassViewSet(viewsets.ModelViewSet):
    serializer_class = ClassSerializer

    def get_queryset(self):
        qs       = Class.objects.filter(is_active=True)
        level_id = self.request.query_params.get('level_id')
        if level_id:
            qs = qs.filter(level_id=level_id)
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['language'] = _get_lang(self.request)
        return context


class SubjectViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectSerializer

    def get_queryset(self):
        lang     = _get_lang(self.request)
        class_id = self.request.query_params.get('class_id')
        qs       = Subject.objects.filter(is_active=True)
        if class_id:
            qs = qs.filter(class_field_id=class_id)
        # ✅ Only return subjects that have units in the requested language
        qs = qs.filter(units__language=lang, units__is_active=True).distinct()
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['language'] = _get_lang(self.request)
        return context


class UnitViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSerializer

    def get_queryset(self):
        lang       = _get_lang(self.request)
        qs         = Unit.objects.filter(language=lang, is_active=True)
        subject_id = self.request.query_params.get('subject_id')
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['language'] = _get_lang(self.request)
        return context


class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer

    def get_queryset(self):
        lang    = _get_lang(self.request)
        qs      = Lesson.objects.filter(language=lang, is_active=True)
        unit_id = self.request.query_params.get('unit_id')
        if unit_id:
            qs = qs.filter(unit_id=unit_id)
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['language'] = _get_lang(self.request)
        return context