from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.db.models import F


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
    title = models.TextField()
    references = models.TextField(blank=True, null=True)
    is_premium = models.BooleanField(default=True)

    def __str__(self):
        return f"Lesson {self.number}: {self.title}"


# -----------------------------
# Plan Constants (5-day week)
# -----------------------------
PLAN_CHOICES = [
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
    ('term', 'Term'),
]

PLAN_DURATIONS = {
    'weekly': 5,      # 5 teaching days per week
    'monthly': 20,    # 4 weeks × 5 days
    'term': 60,       # 12 weeks × 5 days
}

# Max lessons per plan assuming 10 lessons/day
SUBSCRIPTION_LIMITS = {
    'weekly': 50,     # 10 lessons/day × 5 days
    'monthly': 200,   # 10 lessons/day × 20 days
    'term': 600,      # 10 lessons/day × 60 days
}

FREE_LESSON_LIMIT = 3  # Default for guests / non-premium


# -----------------------------
# UserProfile Model
# -----------------------------
# -----------------------------
# UserProfile Model (Secure Default Lesson Limit)
# -----------------------------
class UserProfile(models.Model):
    """
    Hybrid UserProfile (AUTHORITATIVE)
    Supports logged-in users and device-only guests.
    All access decisions flow through this model.
    """

    # Identity
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    device_id = models.CharField(max_length=255, unique=True, null=True, blank=True)

    # Status & Access
    is_active = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)

    can_generate = models.BooleanField(default=True)
    can_download_pdf = models.BooleanField(default=False)
    can_download_docx = models.BooleanField(default=False)
    can_copy_word = models.BooleanField(default=False)

    # Subscription
    subscription_plan = models.CharField(max_length=20, null=True, blank=True, choices=PLAN_CHOICES)
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_expiry = models.DateTimeField(null=True, blank=True)

    # Usage Limits
    # 🔹 CHANGED: enforce default 3 lessons for guests and new non-premium users
    lesson_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="NULL = unlimited / hybrid logic"
    )
    lessons_used = models.PositiveIntegerField(default=0)

    # Prefill Data
    school_name = models.CharField(max_length=255, blank=True, null=True)
    teacher_name = models.CharField(max_length=255, blank=True, null=True)
    default_term = models.CharField(max_length=5, blank=True, null=True)
    class_size = models.PositiveIntegerField(blank=True, null=True)
    references = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Derived Properties
    @property
    def is_guest(self):
        return self.user is None

    def has_unlimited_access(self):
        return self.lesson_limit is None

    # ----------------------
    # Hybrid Access Methods
    # ----------------------
    def get_current_lesson_limit(self):
        # 🔹 CHANGED: guest and new non-premium user fallback to 3
        if self.is_premium and self.subscription_plan:
            return SUBSCRIPTION_LIMITS.get(self.subscription_plan, FREE_LESSON_LIMIT)
        if self.lesson_limit is not None:
            return self.lesson_limit
        return FREE_LESSON_LIMIT  # ensures default of 3

    def can_generate_plan(self):
        if not self.is_active or not self.can_generate:
            return False
        return self.lessons_used < self.get_current_lesson_limit()

    def use_lesson(self):
        if self.is_subscription_active() or self.has_unlimited_access():
            return
        UserProfile.objects.filter(pk=self.pk).update(lessons_used=F('lessons_used') + 1)

    # ----------------------
    # Subscription Logic
    # ----------------------
    def is_subscription_active(self):
        """
        ✅ is_premium=True set by admin = always active (no expiry required)
           is_premium=True with future expiry = active
           is_premium=True with past expiry = NOT active (will be caught by expire_subscription_if_needed)
           is_premium=False = not active
        """
        if not self.is_premium:
            return False
        if self.subscription_expiry:
            return timezone.now() <= self.subscription_expiry
        return True  # ✅ No expiry set = permanent admin grant

    def expire_subscription_if_needed(self):
        """
        Only expire if:
        1. subscription_expiry is explicitly SET (not null)
        2. AND that date is in the past

        ✅ Admin-set is_premium=True with NO expiry date = permanent access
           This is the correct behaviour for manually activated accounts.
        """
        if self.subscription_expiry and timezone.now() > self.subscription_expiry:
            self.is_premium = False
            self.subscription_plan = None
            self.lesson_limit = FREE_LESSON_LIMIT
            self.lessons_used = 0
            self.save(update_fields=['is_premium', 'subscription_plan', 'lesson_limit', 'lessons_used'])


    # ----------------------
    # Admin Control Methods
    # ----------------------
    def activate_premium(self, plan='weekly', reset_usage=True):
        self.is_premium = True
        self.subscription_plan = plan
        self.subscription_start = timezone.now()
        self.subscription_expiry = timezone.now() + timedelta(days=PLAN_DURATIONS.get(plan, 5))
        self.lesson_limit = SUBSCRIPTION_LIMITS.get(plan)
        if reset_usage:
            self.lessons_used = 0
        self.save()

    def deactivate_premium(self):
        self.is_premium = False
        self.subscription_plan = None
        self.subscription_start = None
        self.subscription_expiry = None
        # 🔹 CHANGED: ensure lesson_limit reset to 3 for non-premium users
        self.lesson_limit = FREE_LESSON_LIMIT
        self.lessons_used = 0
        self.save()

    def block_user(self):
        self.is_active = False
        self.save(update_fields=['is_active'])

    def unblock_user(self):
        self.is_active = True
        self.save(update_fields=['is_active'])

    # ----------------------
    # Safety Net
    # ----------------------
    def save(self, *args, **kwargs):
        # 🔹 CHANGED: enforce default 3 lessons if new guest or non-premium user
        if not self.pk:  # new object
            if not self.is_premium and self.lesson_limit is None:
                self.lesson_limit = FREE_LESSON_LIMIT

        if self.pk:
            old = UserProfile.objects.get(pk=self.pk)
            if old.device_id and self.device_id != old.device_id:
                self.device_id = old.device_id

        super().save(*args, **kwargs)

    def __str__(self):
        label = self.user.email if self.user else f"Guest {self.device_id[:8] if self.device_id else 'unknown'}"
        return f"{label} | Premium: {self.is_premium}"


# -----------------------------
# Subscription Model
# -----------------------------
class Subscription(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user_profile} - {self.plan}"

# -----------------------------
# Teaching Strategy Model
# -----------------------------
class TeachingStrategy(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_premium_only = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# -----------------------------
# Strategy-Based Lesson Steps
# -----------------------------
class LessonStrategyStep(models.Model):
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="strategy_steps"
    )

    strategy = models.ForeignKey(
        TeachingStrategy,
        on_delete=models.CASCADE,
        related_name="lesson_steps"
    )

    step_order = models.PositiveIntegerField()
    step_title = models.CharField(max_length=100)
    duration_minutes = models.PositiveIntegerField(default=10)

    teacher_activity = models.TextField()
    learner_activity = models.TextField()
    generic_competence = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["step_order"]

    def __str__(self):
        return f"{self.lesson.title} - {self.strategy.name} - Step {self.step_order}"

class GeneratedLessonPlan(models.Model):
    """
    Persists every lesson plan generated by a logged-in user.
    Guests are skipped (no profile.user → no row saved).
    Used by the dashboard panel for history + bulk ZIP download.
    """
    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='generated_plans'
    )

    # Metadata shown in the dashboard table
    subject      = models.CharField(max_length=100, blank=True)
    unit_title   = models.CharField(max_length=200, blank=True)
    lesson_title = models.CharField(max_length=300, blank=True)
    class_name   = models.CharField(max_length=100, blank=True)
    term         = models.CharField(max_length=10,  blank=True)

    # The full rendered HTML snapshot (for ZIP download)
    html_snapshot = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Generated Lesson Plan'
        verbose_name_plural = 'Generated Lesson Plans'

    def __str__(self):
        return f"{self.profile} | {self.subject} – {self.lesson_title} ({self.created_at:%Y-%m-%d})"
