# File: /lesson-plan-generator/backend/lessons/models.py

from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.db.models import F
from django.contrib.auth.models import User

# ──────────────────────────────────────────────────────────────────────────────
# Cloudinary import — safe for both dev (local storage) and prod (Cloudinary).
# CloudinaryField is only used when USE_CLOUDINARY=True in settings.
# In dev, standard ImageField is used instead so no Cloudinary account needed.
# ──────────────────────────────────────────────────────────────────────────────
USE_CLOUDINARY = getattr(settings, 'USE_CLOUDINARY', False)

if USE_CLOUDINARY:
    from cloudinary.models import CloudinaryField


def image_field(folder, **kwargs):
    """
    Factory that returns the right field type based on environment.

    In dev  (USE_CLOUDINARY=False) → standard Django ImageField
            Images saved to MEDIA_ROOT/folder/ on local disk.

    In prod (USE_CLOUDINARY=True)  → CloudinaryField
            Images uploaded to Cloudinary under the given folder.
            .url still works identically in templates.

    Usage inside a model:
        image = image_field('hero_banners', blank=True, null=True,
                            help_text="Product/brand image …")
    """
    if USE_CLOUDINARY:
        # CloudinaryField does NOT accept upload_to — strip it out first
        kwargs.pop('upload_to', None)
        return CloudinaryField(
            'image',
            folder=folder,
            **kwargs
        )
    else:
        upload_to = kwargs.pop('upload_to', folder + '/')
        return models.ImageField(upload_to=upload_to, **kwargs)


def video_field(folder, **kwargs):
    """
    Same factory for video files.

    In dev  → FileField saved to MEDIA_ROOT/folder/
    In prod → CloudinaryField with resource_type='video'
    """
    if USE_CLOUDINARY:
        # CloudinaryField does NOT accept upload_to — strip it out first
        kwargs.pop('upload_to', None)
        return CloudinaryField(
            'video',
            resource_type='video',
            folder=folder,
            **kwargs
        )
    else:
        upload_to = kwargs.pop('upload_to', folder + '/')
        return models.FileField(upload_to=upload_to, **kwargs)


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
    language  = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='en',
        help_text="Curriculum language this level belongs to"
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"[{self.language.upper()}] {self.name}"


class Class(models.Model):
    level     = models.ForeignKey(Level, related_name='classes', on_delete=models.CASCADE)
    name      = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.level.name} - {self.name}"


class Subject(models.Model):
    class_field = models.ForeignKey(Class, related_name='subjects', on_delete=models.CASCADE)
    name        = models.CharField(max_length=50)
    is_active   = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.class_field.name} - {self.name}"


class Unit(models.Model):
    subject             = models.ForeignKey(Subject, related_name='units', on_delete=models.CASCADE)
    number              = models.PositiveIntegerField()
    title               = models.CharField(max_length=100)
    key_unit_competence = models.TextField()
    total_lessons       = models.PositiveIntegerField(default=0)
    language            = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='en',
        help_text="Language this unit is written in"
    )
    is_active           = models.BooleanField(default=True)

    def __str__(self):
        return f"[{self.language.upper()}] {self.subject.name} - Unit {self.number}: {self.title}"


class Lesson(models.Model):
    unit       = models.ForeignKey(Unit, related_name='lessons', on_delete=models.CASCADE)
    number     = models.PositiveIntegerField()
    title      = models.TextField()
    references = models.TextField(blank=True, null=True)
    language   = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='en',
        help_text="Language this lesson is written in"
    )
    is_premium = models.BooleanField(default=True)
    is_active  = models.BooleanField(default=True)

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
        if self.lesson_limit is not None:
            return self.lesson_limit
        if self.is_premium and self.subscription_plan:
            return SUBSCRIPTION_LIMITS.get(self.subscription_plan, FREE_LESSON_LIMIT)
        return FREE_LESSON_LIMIT

    def can_generate_plan(self):
        if not self.is_active or not self.can_generate:
            return False
        return self.lessons_used < self.get_current_lesson_limit()

    def use_lesson(self):
        if self.is_subscription_active() or self.has_unlimited_access():
            return
        UserProfile.objects.filter(pk=self.pk).update(lessons_used=F('lessons_used') + 1)

    def is_subscription_active(self):
        if not self.is_premium:
            return False
        if self.subscription_expiry:
            return timezone.now() <= self.subscription_expiry
        return True

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
        if not self.pk:
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
        ordering        = ["step_order"]
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
        ordering            = ['-created_at']
        verbose_name        = 'Generated Lesson Plan'
        verbose_name_plural = 'Generated Lesson Plans'

    def __str__(self):
        return f"{self.profile} | {self.subject} – {self.lesson_title} ({self.created_at:%Y-%m-%d})"


# -----------------------------
# Manual Payment Proof
# ─────────────────────────────
# screenshot field:
#   dev  → ImageField  → saved to MEDIA_ROOT/payment_proofs/YYYY/MM/
#   prod → CloudinaryField → uploaded to Cloudinary folder payment_proofs/
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

    # ── storage-aware screenshot field ──────────────────────────────────────
    screenshot   = image_field(
        'payment_proofs',
        upload_to='payment_proofs/%Y/%m/',   # only used by ImageField in dev
        blank=True,
        null=True,
        help_text="MoMo / bank transfer screenshot."
    )
    # ────────────────────────────────────────────────────────────────────────

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


class ChatHistory(models.Model):
    user            = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    conversation_id = models.CharField(max_length=100)
    message         = models.TextField()
    direction       = models.CharField(max_length=10)  # 'incoming' or 'outgoing'
    intent          = models.CharField(max_length=50, null=True)
    created_at      = models.DateTimeField(auto_now_add=True)


class Interaction(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    intent       = models.CharField(max_length=50)
    user_message = models.TextField()
    bot_response = models.TextField()
    satisfied    = models.BooleanField(null=True)
    timestamp    = models.DateTimeField(auto_now_add=True)


class BotConfig(models.Model):
    """Dynamic configuration — change bot behavior without redeploying"""
    key        = models.CharField(max_length=100, unique=True)
    value      = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get(cls, key, default=None):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default


class BotResponse(models.Model):
    """Admin-editable bot responses"""
    intent            = models.CharField(max_length=50, unique=True)
    response_template = models.TextField(help_text="Use {username}, {remaining}, etc.")
    is_active         = models.BooleanField(default=True)
    priority          = models.IntegerField(default=1)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.intent} - {'Active' if self.is_active else 'Inactive'}"


class QuickReply(models.Model):
    """Quick reply buttons that appear in chat"""
    text       = models.CharField(max_length=100, help_text="Button text shown to user")
    message    = models.CharField(max_length=500, help_text="Message sent to bot when clicked")
    icon       = models.CharField(max_length=10, blank=True, help_text="Emoji icon (e.g., 📝, 💰)")
    order      = models.IntegerField(default=0, help_text="Display order")
    row        = models.IntegerField(default=1, help_text="Which row (1 or 2)")
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering       = ['row', 'order']
        verbose_name_plural = "Quick replies"

    def __str__(self):
        return f"{self.icon} {self.text}"


# =============================================================================
# AD MODELS
# =============================================================================
# Image / video storage:
#   dev  (USE_CLOUDINARY=False) → files saved to MEDIA_ROOT on local disk
#   prod (USE_CLOUDINARY=True)  → files uploaded to Cloudinary via API
#
# Template usage is IDENTICAL in both cases — {{ obj.image.url }} works.
# =============================================================================


class TopBanner(models.Model):
    """
    Scrolling ticker announcement shown at the very top of the page.
    No image/video on this model — text + colours only.

    Admin controls
    ──────────────
    • text          → the announcement sentence
    • icon          → emoji prefix e.g. 🎓
    • badge         → short pill label e.g. NEW, HOT, SALE
    • badge_color   → pill background colour (hex)
    • color         → optional text colour override (hex)
    • bg            → optional whole-item background override (hex)
    • url           → click destination (use '#' for no link)
    • scroll_speed  → ticker animation duration in seconds
                      10 = very fast | 44 = default | 120 = very slow
    • show_on_*     → tick which pages display this banner
    • order         → lower number = appears first in the ticker
    • active        → uncheck to hide without deleting
    """

    text        = models.CharField(
        max_length=300,
        help_text="Announcement text scrolling across the ticker."
    )
    url         = models.CharField(
        max_length=500, blank=True, default='#',
        help_text="Click destination URL. Use '#' for no link."
    )
    icon        = models.CharField(
        max_length=10, blank=True, default='',
        help_text="Emoji icon e.g. 🎓  📚  🏫"
    )
    badge       = models.CharField(
        max_length=20, blank=True, default='',
        help_text="Short ribbon label e.g. NEW, HOT, SALE — leave blank for none."
    )
    badge_color = models.CharField(
        max_length=20, blank=True, default='#e74c3c',
        help_text="Badge background colour (hex) e.g. #e74c3c"
    )
    color       = models.CharField(
        max_length=20, blank=True, default='',
        help_text="Text colour override e.g. #ffd700 — leave blank for default gold."
    )
    bg          = models.CharField(
        max_length=20, blank=True, default='',
        help_text="Item background colour override e.g. #1a3a2a — leave blank for default dark."
    )
    scroll_speed = models.PositiveIntegerField(
        default=44,
        help_text=(
            "Ticker animation duration in seconds. "
            "Lower = faster.  10 = very fast | 44 = default | 120 = very slow. "
            "Only the first active banner's speed is used for all banners."
        )
    )

    show_on_landing = models.BooleanField(default=True,  help_text="Show on the Landing page.")
    show_on_index   = models.BooleanField(default=True,  help_text="Show on the Index / Dashboard page.")
    show_on_pricing = models.BooleanField(default=False, help_text="Show on the Pricing page.")

    order      = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")
    active     = models.BooleanField(default=True, help_text="Uncheck to hide without deleting.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['order', 'created_at']
        verbose_name        = 'Top Banner'
        verbose_name_plural = 'Top Banners'

    def __str__(self):
        pages = [p for p, f in [('landing', self.show_on_landing), ('index', self.show_on_index), ('pricing', self.show_on_pricing)] if f]
        return f"[{'ON' if self.active else 'OFF'}] [{', '.join(pages) or 'no pages'}] {self.text[:60]}"


class HeroBanner(models.Model):
    """
    Full-width hero carousel slide shown directly below the ticker.

    image field storage:
        dev  → ImageField  → MEDIA_ROOT/hero_banners/
        prod → CloudinaryField → Cloudinary folder: hero_banners/

    Admin controls
    ──────────────
    • headline      → big bold title
    • description   → supporting sentence (optional)
    • cta_text      → button label
    • cta_url       → button destination URL
    • image         → product/brand image shown on the RIGHT side
    • badge         → small pill above headline
    • badge_color   → pill background colour (hex)
    • bg_color      → left/top gradient colour
    • bg_color2     → right/bottom gradient colour
    • duration      → seconds this slide stays before auto-advancing
    • show_on_*     → tick which pages display this slide
    • order         → lower number = appears earlier in carousel
    • active        → uncheck to hide without deleting
    """

    headline    = models.CharField(
        max_length=120,
        help_text="Big title text e.g. 'Get 50% Off CBC Mathematics Books'"
    )
    description = models.CharField(
        max_length=250, blank=True, default='',
        help_text="Supporting sentence shown below the headline (optional)."
    )
    cta_text    = models.CharField(
        max_length=40, blank=True, default='Learn More',
        help_text="Button label e.g. Shop Now, Get Started, Download Free."
    )
    cta_url     = models.CharField(
        max_length=500, blank=True, default='#',
        help_text="Button destination URL e.g. https://affiliate.com/link"
    )

    # ── storage-aware image field ────────────────────────────────────────────
    image = image_field(
        'hero_banners',
        upload_to='hero_banners/',   # only used by ImageField in dev
        blank=True,
        null=True,
        help_text=(
            "Product/brand image shown on the right side of the slide. "
            "dev: saved locally | prod: uploaded to Cloudinary."
        )
    )
    # ────────────────────────────────────────────────────────────────────────

    badge       = models.CharField(
        max_length=20, blank=True, default='',
        help_text="Small pill above headline e.g. SALE, NEW, HOT — leave blank for none."
    )
    badge_color = models.CharField(
        max_length=20, blank=True, default='#f5c518',
        help_text="Badge background colour (hex) e.g. #f5c518 (gold), #e74c3c (red)."
    )
    bg_color    = models.CharField(
        max_length=20, default='#0d1b2a',
        help_text="Left / top gradient colour e.g. #0d1b2a (dark blue)."
    )
    bg_color2   = models.CharField(
        max_length=20, default='#1a3a5c',
        help_text="Right / bottom gradient colour e.g. #1a3a5c (teal blue)."
    )
    duration    = models.PositiveIntegerField(
        default=8,
        help_text=(
            "Seconds this slide stays visible before auto-advancing. "
            "3 = snappy | 8 = default | 15 = relaxed | 30 = very slow."
        )
    )

    show_on_landing = models.BooleanField(default=True,  help_text="Show on the Landing page.")
    show_on_index   = models.BooleanField(default=True,  help_text="Show on the Index / Dashboard page.")
    show_on_pricing = models.BooleanField(default=False, help_text="Show on the Pricing page.")

    order      = models.PositiveIntegerField(default=0, help_text="Lower numbers appear earlier in the carousel.")
    active     = models.BooleanField(default=True, help_text="Uncheck to hide without deleting.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['order', 'created_at']
        verbose_name        = 'Hero Banner'
        verbose_name_plural = 'Hero Banners'

    def __str__(self):
        pages = [p for p, f in [('landing', self.show_on_landing), ('index', self.show_on_index), ('pricing', self.show_on_pricing)] if f]
        return f"[{'ON' if self.active else 'OFF'}] [{', '.join(pages) or 'no pages'}] {self.headline[:60]}"


class BottomAd(models.Model):
    """
    Photo card shown in the fixed bottom ad strip.

    image field storage:
        dev  → ImageField  → MEDIA_ROOT/bottom_ads/
        prod → CloudinaryField → Cloudinary folder: bottom_ads/

    Admin controls
    ──────────────
    • title         → headline shown on hover overlay
    • subtitle      → short description shown on hover (optional)
    • image         → card photo — square or portrait, 200×200 px minimum
    • url           → click destination URL
    • badge         → corner ribbon text e.g. SALE, NEW, HOT
    • badge_color   → ribbon background colour (hex)
    • show_on_*     → tick which pages display this card
    • order         → lower number = appears further left in the strip
    • active        → uncheck to hide without deleting
    """

    title    = models.CharField(
        max_length=120,
        help_text="Headline shown on the hover overlay e.g. 'Mathematics Grade 5'."
    )
    subtitle = models.CharField(
        max_length=200, blank=True, default='',
        help_text="Short description on hover e.g. 'CBC-aligned workbook' (optional)."
    )

    # ── storage-aware image field ────────────────────────────────────────────
    image = image_field(
        'bottom_ads',
        upload_to='bottom_ads/',   # only used by ImageField in dev
        help_text=(
            "Card photo. Square or portrait, 200×200 px minimum. "
            "dev: saved locally | prod: uploaded to Cloudinary."
        )
    )
    # ────────────────────────────────────────────────────────────────────────

    url         = models.CharField(
        max_length=500, blank=True, default='#',
        help_text="Click destination URL e.g. https://affiliate.com/product"
    )
    badge       = models.CharField(
        max_length=20, blank=True, default='',
        help_text="Corner ribbon text e.g. SALE, NEW, HOT — leave blank for none."
    )
    badge_color = models.CharField(
        max_length=20, blank=True, default='#e74c3c',
        help_text="Ribbon background colour (hex) e.g. #e74c3c (red), #27AE60 (green)."
    )

    show_on_landing = models.BooleanField(default=True,  help_text="Show on the Landing page.")
    show_on_index   = models.BooleanField(default=True,  help_text="Show on the Index / Dashboard page.")
    show_on_pricing = models.BooleanField(default=False, help_text="Show on the Pricing page.")

    order      = models.PositiveIntegerField(default=0, help_text="Lower numbers appear further left.")
    active     = models.BooleanField(default=True, help_text="Uncheck to hide without deleting.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['order', 'created_at']
        verbose_name        = 'Bottom Ad'
        verbose_name_plural = 'Bottom Ads'

    def __str__(self):
        pages = [p for p, f in [('landing', self.show_on_landing), ('index', self.show_on_index), ('pricing', self.show_on_pricing)] if f]
        return f"[{'ON' if self.active else 'OFF'}] [{', '.join(pages) or 'no pages'}] {self.title}"