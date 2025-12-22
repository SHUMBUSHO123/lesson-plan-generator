from rest_framework import serializers
from .models import Level, Class, Subject, Unit, Lesson

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'

class UnitSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Unit
        fields = '__all__'

class SubjectSerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True, read_only=True)

    class Meta:
        model = Subject
        fields = '__all__'

class ClassSerializer(serializers.ModelSerializer):
    subjects = SubjectSerializer(many=True, read_only=True)

    class Meta:
        model = Class
        fields = '__all__'

class LevelSerializer(serializers.ModelSerializer):
    classes = ClassSerializer(many=True, read_only=True)

    class Meta:
        model = Level
        fields = '__all__'
