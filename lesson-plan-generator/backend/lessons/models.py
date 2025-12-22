
from django.db import models
from django.utils import timezone
from datetime import timedelta

# -----------------------------
# Core Models for Lesson Plans
# -----------------------------

# Level model
class Level(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

# Class model
class Class(models.Model):
    level = models.ForeignKey(Level, related_name='classes', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.level.name} - {self.name}"

# Subject model
class Subject(models.Model):
    class_field = models.ForeignKey(Class, related_name='subjects', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.class_field.name} - {self.name}"

# Unit model
class Unit(models.Model):
    subject = models.ForeignKey(Subject, related_name='units', on_delete=models.CASCADE)
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=100)
    key_unit_competence = models.TextField()
    total_lessons = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.subject.name} - Unit {self.number}: {self.title}"

# Lesson model
class Lesson(models.Model):
    unit = models.ForeignKey(Unit, related_name='lessons', on_delete=models.CASCADE)
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=100)
    references = models.TextField(blank=True, null=True)
    is_premium = models.BooleanField(default=True)  # All lessons premium by default

    def __str__(self):
        return f"Lesson {self.number}: {self.title}"

# -----------------------------
# Device-based Premium Access
# -----------------------------
class DeviceAccess(models.Model):
    device_id = models.CharField(max_length=255, unique=True)
    free_plans_used = models.IntegerField(default=0)
    premium_active = models.BooleanField(default=False)
    premium_start = models.DateTimeField(null=True, blank=True)
    premium_expiry = models.DateTimeField(null=True, blank=True)

    def check_status(self):
        """Reset access if premium expired"""
        if self.premium_expiry and timezone.now() > self.premium_expiry:
            self.premium_active = False
            self.free_plans_used = 0
            self.premium_start = None
            self.premium_expiry = None
            self.save()

    def can_generate_plan(self):
        """Check if device can generate a lesson plan"""
        self.check_status()
        if self.premium_active:
            return True
        elif self.free_plans_used < 3:
            return True
        else:
            return False

    def use_plan(self):
        """Increment free plan usage"""
        self.check_status()
        if not self.premium_active:
            self.free_plans_used += 1
            self.save()

    def activate_premium(self):
        """Activate premium access for 90 days"""
        self.premium_active = True
        self.premium_start = timezone.now()
        self.premium_expiry = timezone.now() + timedelta(days=90)
        self.save()

    def __str__(self):
        return f"Device {self.device_id} | Premium: {self.premium_active} | Free plans used: {self.free_plans_used}"
