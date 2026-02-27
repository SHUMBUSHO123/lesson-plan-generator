# File: /lesson-plan-generator/backend/lessons/serializers.py

from rest_framework import serializers
from .models import Level, Class, Subject, Unit, Lesson


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Lesson
        fields = '__all__'


class UnitSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField()

    class Meta:
        model  = Unit
        fields = '__all__'

    def get_lessons(self, obj):
        lang = self.context.get('language', 'en')
        lessons = obj.lessons.filter(is_active=True, language=lang)
        return LessonSerializer(lessons, many=True, context=self.context).data


class SubjectSerializer(serializers.ModelSerializer):
    units = serializers.SerializerMethodField()

    class Meta:
        model  = Subject
        fields = '__all__'

    def get_units(self, obj):
        lang  = self.context.get('language', 'en')
        units = obj.units.filter(is_active=True, language=lang)
        return UnitSerializer(units, many=True, context=self.context).data


class ClassSerializer(serializers.ModelSerializer):
    subjects = serializers.SerializerMethodField()

    class Meta:
        model  = Class
        fields = '__all__'

    def get_subjects(self, obj):
        lang = self.context.get('language', 'en')
        # ✅ Only subjects with units in this language
        subjects = obj.subjects.filter(
            is_active=True,
            units__language=lang,
            units__is_active=True
        ).distinct()
        # Subject has no language field — just filter active
        return SubjectSerializer(subjects, many=True, context=self.context).data


class LevelSerializer(serializers.ModelSerializer):
    classes = serializers.SerializerMethodField()

    class Meta:
        model  = Level
        fields = '__all__'

    def get_classes(self, obj):
        # Class has no language field — just filter active
        classes = obj.classes.filter(is_active=True)
        return ClassSerializer(classes, many=True, context=self.context).data