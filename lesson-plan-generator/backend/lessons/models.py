# File: /lesson-plan-generator/backend/lessons/models.py

from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.db.models import F


# -----------------------------
# Core Models for Lesson Plans
# -----------------------------

# ─────────────────────────────────────────────────────────────────────────────
# Language support
# Added to support Kinyarwanda, Kiswahili, French alongside existing English.
# Each language has its own seeder that creates rows tagged with its code.
# Filtering by language at query time returns only that language's curriculum.
# ─────────────────────────────────────────────────────────────────────────────
LANGUAGE_CHOICES = [
    ('en', 'English'),
    ('rw', 'Kinyarwanda'),
    ('sw', 'Kiswahili'),
    ('fr', 'French'),
]


class Level(models.Model):
    name      = models.CharField(max_length=50)
    language  = models.CharField(                        # ← NEW
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='en',
        help_text="Curriculum language this level belongs to"
    )
    is_active = models.BooleanField(default=True)        # ✅ Soft delete

    def __str__(self):
        return f"[{self.language.upper()}] {self.name}"


class Class(models.Model):
    level     = models.ForeignKey(Level, related_name='classes', on_delete=models.CASCADE)
    name      = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)        # ✅ Soft delete

    def __str__(self):
        return f"{self.level.name} - {self.name}"


class Subject(models.Model):
    class_field = models.ForeignKey(Class, related_name='subjects', on_delete=models.CASCADE)
    name        = models.CharField(max_length=50)
    is_active   = models.BooleanField(default=True)      # ✅ Soft delete

    def __str__(self):
        return f"{self.class_field.name} - {self.name}"


class Unit(models.Model):
    subject             = models.ForeignKey(Subject, related_name='units', on_delete=models.CASCADE)
    number              = models.PositiveIntegerField()
    title               = models.CharField(max_length=100)
    key_unit_competence = models.TextField()
    total_lessons       = models.PositiveIntegerField(default=0)
    language            = models.CharField(             # ← NEW
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='en',
        help_text="Language this unit is written in"
    )
    is_active           = models.BooleanField(default=True)  # ✅ Soft delete

    def __str__(self):
        return f"[{self.language.upper()}] {self.subject.name} - Unit {self.number}: {self.title}"


class Lesson(models.Model):
    unit       = models.ForeignKey(Unit, related_name='lessons', on_delete=models.CASCADE)
    number     = models.PositiveIntegerField()
    title      = models.TextField()
    references = models.TextField(blank=True, null=True)
    language   = models.CharField(                      # ← NEW
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='en',
        help_text="Language this lesson is written in"
    )
    is_premium = models.BooleanField(default=True)
    is_active  = models.BooleanField(default=True)      # ✅ Soft delete

    def __str__(self):
        return f"[{self.language.upper()}] Lesson {self.number}: {self.title}"


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

SUBSCRIPTION_LIMITS = {
    'weekly': 50,     # 10 lessons/day × 5 days
    'monthly': 200,   # 10 lessons/day × 20 days
    'term': 600,      # 10 lessons/day × 60 days
}

FREE_LESSON_LIMIT = 3  # Default for guests / non-premium


# -----------------------------
# UserProfile Model
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
    is_active         = models.BooleanField(default=True)
    is_premium        = models.BooleanField(default=False)

    can_generate      = models.BooleanField(default=True)
    can_download_pdf  = models.BooleanField(default=False)
    can_download_docx = models.BooleanField(default=False)
    can_copy_word     = models.BooleanField(default=False)

    # Subscription
    subscription_plan   = models.CharField(max_length=20, null=True, blank=True, choices=PLAN_CHOICES)
    subscription_start  = models.DateTimeField(null=True, blank=True)
    subscription_expiry = models.DateTimeField(null=True, blank=True)

    # Usage Limits
    lesson_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="NULL = unlimited / hybrid logic"
    )
    lessons_used = models.PositiveIntegerField(default=0)

    # Prefill Data
    school_name  = models.CharField(max_length=255, blank=True, null=True)
    teacher_name = models.CharField(max_length=255, blank=True, null=True)
    default_term = models.CharField(max_length=5, blank=True, null=True)
    class_size   = models.PositiveIntegerField(blank=True, null=True)
    references   = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_guest(self):
        return self.user is None

    def has_unlimited_access(self):
        return self.lesson_limit is None

    def get_current_lesson_limit(self):
        """
        FIX: Always respect manually set lesson_limit first.
        This allows admin to override limits (e.g. give 100 lessons
        instead of the plan default 50) without it being overwritten.
        Only falls back to plan default if lesson_limit is NULL.
        """
        # ① Admin manually set a specific limit — always use it
        if self.lesson_limit is not None:
            return self.lesson_limit
        # ② No manual limit — fall back to plan default
        if self.is_premium and self.subscription_plan:
            return SUBSCRIPTION_LIMITS.get(self.subscription_plan, FREE_LESSON_LIMIT)
        # ③ Free user with no limit set
        return FREE_LESSON_LIMIT

    def can_generate_plan(self):
        if not self.is_active or not self.can_generate:
            return False
        return self.lessons_used < self.get_current_lesson_limit()

    def use_lesson(self):
        """
        Increment lesson counter.
        Premium users with active subscription skip increment —
        their counter is managed separately via use_lesson_atomic.
        """
        if self.is_subscription_active() or self.has_unlimited_access():
            return
        UserProfile.objects.filter(pk=self.pk).update(lessons_used=F('lessons_used') + 1)

    def is_subscription_active(self):
        if not self.is_premium:
            return False
        if self.subscription_expiry:
            return timezone.now() <= self.subscription_expiry
        return True  # No expiry = permanent admin grant

    def expire_subscription_if_needed(self):
        if self.subscription_expiry and timezone.now() > self.subscription_expiry:
            self.is_premium        = False
            self.subscription_plan = None
            self.lesson_limit      = FREE_LESSON_LIMIT
            self.lessons_used      = 0
            self.save(update_fields=['is_premium', 'subscription_plan', 'lesson_limit', 'lessons_used'])

    def activate_premium(self, plan='weekly', reset_usage=True):
        self.is_premium         = True
        self.subscription_plan  = plan
        self.subscription_start = timezone.now()
        self.subscription_expiry = timezone.now() + timedelta(days=PLAN_DURATIONS.get(plan, 5))
        self.lesson_limit       = SUBSCRIPTION_LIMITS.get(plan)
        if reset_usage:
            self.lessons_used = 0
        self.save()

    def deactivate_premium(self):
        self.is_premium          = False
        self.subscription_plan   = None
        self.subscription_start  = None
        self.subscription_expiry = None
        self.lesson_limit        = FREE_LESSON_LIMIT
        self.lessons_used        = 0
        self.save()

    def block_user(self):
        self.is_active = False
        self.save(update_fields=['is_active'])

    def unblock_user(self):
        self.is_active = True
        self.save(update_fields=['is_active'])

    def save(self, *args, **kwargs):
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
    plan         = models.CharField(max_length=20, choices=PLAN_CHOICES)
    start_date   = models.DateTimeField(auto_now_add=True)
    end_date     = models.DateTimeField()
    active       = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user_profile} - {self.plan}"


# -----------------------------
# Teaching Strategy Model
# -----------------------------
class TeachingStrategy(models.Model):
    name            = models.CharField(max_length=100)
    description     = models.TextField(blank=True, null=True)
    is_premium_only = models.BooleanField(default=False)
    is_active       = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# -----------------------------
# Strategy-Based Lesson Steps
# -----------------------------
class LessonStrategyStep(models.Model):
    lesson   = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="strategy_steps"
    )
    strategy = models.ForeignKey(
        TeachingStrategy, on_delete=models.CASCADE, related_name="lesson_steps"
    )

    step_order               = models.PositiveIntegerField()
    step_title               = models.CharField(max_length=100)
    duration_minutes         = models.PositiveIntegerField(default=10)

    teacher_activity         = models.TextField()
    learner_activity         = models.TextField()
    generic_competence       = models.TextField(blank=True, null=True)
    competence_integration   = models.TextField(
        blank=True, null=True,
        help_text="Explains HOW the competence is developed in this specific step"
    )
    lesson_description       = models.TextField(
        blank=True, null=True,
        help_text="1-2 sentence summary of lesson (only in step 1)"
    )
    instructional_objective  = models.TextField(
        blank=True, null=True,
        help_text="Professional ABCD format objective (only in step 1)"
    )
    cross_cutting_issues     = models.TextField(
        blank=True, null=True,
        help_text="CBC cross-cutting issues integration (only in step 1)"
    )

    class Meta:
        ordering      = ["step_order"]
        unique_together = ["lesson", "strategy", "step_order"]

    def __str__(self):
        return f"{self.lesson.title} - {self.strategy.name} - Step {self.step_order}"


# -----------------------------
# Generated Lesson Plan
# -----------------------------
class GeneratedLessonPlan(models.Model):
    """
    Persists every lesson plan generated by a logged-in user.
    Guests are skipped (no profile.user → no row saved).
    Used by the dashboard panel for history + bulk ZIP download.
    """
    profile       = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name='generated_plans'
    )
    subject       = models.CharField(max_length=100, blank=True)
    unit_title    = models.CharField(max_length=200, blank=True)
    lesson_title  = models.CharField(max_length=300, blank=True)
    class_name    = models.CharField(max_length=100, blank=True)
    term          = models.CharField(max_length=10,  blank=True)
    html_snapshot = models.TextField()
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering         = ['-created_at']
        verbose_name     = 'Generated Lesson Plan'
        verbose_name_plural = 'Generated Lesson Plans'

    def __str__(self):
        return f"{self.profile} | {self.subject} – {self.lesson_title} ({self.created_at:%Y-%m-%d})"


# -----------------------------
# Manual Payment Proof
# -----------------------------
class ManualPaymentProof(models.Model):

    PLAN_CHOICES = [
        ('weekly',  'Weekly — 200 RWF'),
        ('monthly', 'Monthly — 500 RWF'),
        ('term',    'Term — 1000 RWF'),
    ]

    STATUS_CHOICES = [
        ('pending',  '⏳ Pending'),
        ('approved', '✅ Approved'),
        ('rejected', '❌ Rejected'),
    ]

    user         = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='payment_proofs'
    )
    full_name    = models.CharField(max_length=150)
    phone        = models.CharField(max_length=20,  blank=True, null=True)
    plan         = models.CharField(max_length=20, choices=PLAN_CHOICES, default='monthly')
    tx_id        = models.CharField(max_length=100, blank=True, null=True)
    amount       = models.CharField(max_length=20,  blank=True, null=True)
    screenshot   = models.ImageField(upload_to='payment_proofs/%Y/%m/', blank=True, null=True)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note   = models.TextField(blank=True, help_text='Optional note when approving or rejecting')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering             = ['-submitted_at']
        verbose_name         = 'Manual Payment Proof'
        verbose_name_plural  = 'Manual Payment Proofs'

    def __str__(self):
        return f"{self.full_name} | {self.plan} | {self.status}"


# =============================================================================
# ✅ SOFT DELETE — QUERY REFERENCE
# =============================================================================
# After running migrations, update ALL views/querysets to filter active only:
#
#   Level.objects.filter(is_active=True)
#   Class.objects.filter(level=selected_level, is_active=True)
#   Subject.objects.filter(class_field=selected_class, is_active=True)
#   Unit.objects.filter(subject=selected_subject, is_active=True)
#   Lesson.objects.filter(unit=selected_unit, is_active=True)
#
# To deactivate (soft delete) any record from Django Admin:
#   → Open the record → Uncheck "Is active" → Save
#   → Data is preserved; it simply won't appear in filtered queries.
#
# =============================================================================
# ✅ LANGUAGE FILTER — QUERY REFERENCE
# =============================================================================
# When fetching curriculum data, always filter by language:
#
#   Level.objects.filter(language='en', is_active=True)   # English
#   Level.objects.filter(language='rw', is_active=True)   # Kinyarwanda
#   Level.objects.filter(language='sw', is_active=True)   # Kiswahili
#   Level.objects.filter(language='fr', is_active=True)   # French
#
# Unit and Lesson also carry language so you can query either way:
#   Unit.objects.filter(language='rw', is_active=True)
#   Lesson.objects.filter(unit=unit, language='rw', is_active=True)
#
# Existing English data is safe — default='en' on all new fields means
# every existing row automatically gets language='en' after migration.
# =============================================================================