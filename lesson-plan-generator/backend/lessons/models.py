# File: /lesson-plan-generator/backend/lessons/models.py

from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User

# -----------------------------
# Core Models for Lesson Plans
# -----------------------------

class Level(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Class(models.Model):
    level = models.ForeignKey(Level, related_name='classes', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.level.name} - {self.name}"


class Subject(models.Model):
    class_field = models.ForeignKey(Class, related_name='subjects', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.class_field.name} - {self.name}"


class Unit(models.Model):
    subject = models.ForeignKey(Subject, related_name='units', on_delete=models.CASCADE)
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=100)
    key_unit_competence = models.TextField()
    total_lessons = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.subject.name} - Unit {self.number}: {self.title}"


class Lesson(models.Model):
    unit = models.ForeignKey(Unit, related_name='lessons', on_delete=models.CASCADE)
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=100)
    references = models.TextField(blank=True, null=True)
    is_premium = models.BooleanField(default=True)

    def __str__(self):
        return f"Lesson {self.number}: {self.title}"


# -----------------------------
# Device-based Premium Access
# -----------------------------

PLAN_CHOICES = [
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
    ('term', 'Term'),
]

class UserProfile(models.Model):
    """
    Hybrid UserProfile: supports registered users (email/login) and device-only guests.
    Fully admin-controllable with premium status, dynamic limits, feature flags, and date restrictions.
    """
    # ===== HYBRID IDENTIFICATION =====
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    device_id = models.CharField(max_length=255, unique=True)

    # ===== STATUS & SUBSCRIPTION =====
    is_active = models.BooleanField(default=True)   # block user completely
    is_premium = models.BooleanField(default=False)
    subscription_plan = models.CharField(max_length=20, choices=PLAN_CHOICES, null=True, blank=True)
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_expiry = models.DateTimeField(null=True, blank=True)
    premium_active = models.BooleanField(default=False)
    premium_start = models.DateTimeField(null=True, blank=True)
    premium_expiry = models.DateTimeField(null=True, blank=True)
    

    # ===== DYNAMIC LIMITS =====
    lesson_limit = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="NULL = unlimited lessons"
    )
    lessons_used = models.PositiveIntegerField(default=0)

    # ===== FEATURE FLAGS =====
    can_generate = models.BooleanField(default=True)
    can_download_pdf = models.BooleanField(default=False)
    can_download_docx = models.BooleanField(default=False)
    can_copy_word = models.BooleanField(default=False)
    allow_future_dates = models.BooleanField(default=False)

    # ===== GUEST TRACKING =====
    free_plans_used = models.PositiveIntegerField(default=0)

    # ===== TIMESTAMPS =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # -------------------------
    # HELPERS / BUSINESS LOGIC
    # -------------------------
    def is_guest(self):
        return self.user is None

    def has_unlimited_access(self):
        return self.lesson_limit is None

    def check_subscription_status(self):
        """Automatically deactivate premium if expired."""
        if self.subscription_expiry and timezone.now() > self.subscription_expiry:
            self.is_premium = False
            self.subscription_plan = None
            self.subscription_start = None
            self.subscription_expiry = None
            self.free_plans_used = 0
            self.save()

    def can_generate_plan(self):
        """Check if the user/guest can generate a lesson."""
        self.check_subscription_status()
        if not self.is_active or not self.can_generate:
            return False
        if self.is_premium:
            return True
        # For free/guest users, use lesson limit or free_plans_used
        if self.has_unlimited_access():
            return True
        return self.lessons_used < self.lesson_limit

    def use_lesson(self):
        """Increment lesson usage when generating a lesson plan."""
        self.check_subscription_status()
        if self.is_premium:
            return
        if self.has_unlimited_access():
            return
        self.lessons_used += 1
        self.save()

    def activate_premium(self, days, plan=None):
        """Activate premium access for a given number of days."""
        self.is_premium = True
        self.subscription_start = timezone.now()
        self.subscription_expiry = timezone.now() + timedelta(days=days)
        self.subscription_plan = plan
        self.save()

    def block_user(self):
        """Admin can block user completely."""
        self.is_active = False
        self.save()

    def unblock_user(self):
        """Admin can unblock user."""
        self.is_active = True
        self.save()

    def __str__(self):
        if self.user:
            return f"{self.user.email} | Premium: {self.is_premium}"
        return f"Guest ({self.device_id[:8]}) | Premium: {self.is_premium}"


class Subscription(models.Model):
    user_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="subscriptions"
    )
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user_profile.user.email} - {self.plan}"
