# File: /lesson-plan-generator/backend/lessons/admin.py

from datetime import timedelta
from django.utils import timezone
from django.contrib import admin
from django import forms
from django.utils.html import format_html, mark_safe
from .models import (
    Level,
    Class,
    ManualPaymentProof,
    Subject,
    Unit,
    Lesson,
    UserProfile,
    Subscription,
    TeachingStrategy,
    LessonStrategyStep,
    GeneratedLessonPlan,
    PLAN_DURATIONS,
    SUBSCRIPTION_LIMITS,
)


# ===============================
# INLINE MODELS
# ===============================
class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ('number', 'title', 'references', 'is_premium')
    show_change_link = True


class UnitInline(admin.TabularInline):
    model = Unit
    extra = 0
    fields = ('number', 'title', 'key_unit_competence', 'total_lessons')
    show_change_link = True


class SubjectInline(admin.TabularInline):
    model = Subject
    extra = 0
    fields = ('name',)
    show_change_link = True


class ClassInline(admin.TabularInline):
    model = Class
    extra = 0
    fields = ('name',)
    show_change_link = True


# ===============================
# MODEL ADMINS
# ===============================
@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
    search_fields = ('name',)
    inlines = [ClassInline]


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'level')
    list_filter = ('level',)
    search_fields = ('name',)
    inlines = [SubjectInline]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'class_field')
    list_filter = ('class_field__level', 'class_field')
    search_fields = ('name',)
    inlines = [UnitInline]


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('title', 'number', 'subject', 'total_lessons')
    list_filter = (
        'subject__class_field__level',
        'subject__class_field',
        'subject'
    )
    search_fields = ('title',)
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'number', 'unit',
        'subject_name', 'class_name', 'level_name', 'is_premium'
    )
    list_filter = (
        'unit__subject__class_field__level',
        'unit__subject__class_field',
        'unit__subject'
    )
    search_fields = ('title',)

    def subject_name(self, obj):
        return obj.unit.subject.name
    subject_name.short_description = 'Subject'

    def class_name(self, obj):
        return obj.unit.subject.class_field.name
    class_name.short_description = 'Class'

    def level_name(self, obj):
        return obj.unit.subject.class_field.level.name
    level_name.short_description = 'Level'


# ===============================
# ADMIN ACTIONS
# ===============================
@admin.action(description="✅ Activate selected users for premium (default weekly)")
def activate_selected_premium(modeladmin, request, queryset):
    activated_count = 0
    for profile in queryset:
        plan = profile.subscription_plan or 'weekly'
        profile.activate_premium(plan=plan, reset_usage=True)
        activated_count += 1
    modeladmin.message_user(
        request,
        f"✅ Activated premium for {activated_count} user(s)."
    )


@admin.action(description="🚫 Deactivate premium for selected users")
def deactivate_selected_premium(modeladmin, request, queryset):
    deactivated_count = 0
    for profile in queryset:
        profile.deactivate_premium()
        deactivated_count += 1
    modeladmin.message_user(
        request,
        f"🚫 Deactivated premium for {deactivated_count} user(s)."
    )


# ===============================
# GUEST FILTER
# ===============================
class GuestFilter(admin.SimpleListFilter):
    title = 'Account Type'
    parameter_name = 'account_type'

    def lookups(self, request, model_admin):
        return (
            ('registered', '👤 Registered Users'),
            ('guest',      '👻 Guests (device only)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'registered':
            return queryset.filter(user__isnull=False)
        if self.value() == 'guest':
            return queryset.filter(user__isnull=True)
        return queryset


# ===============================
# USER PROFILE FORM
# ===============================
class UserProfileAdminForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['subscription_start', 'subscription_expiry', 'lesson_limit']:
            if field in self.fields:
                self.fields[field].required = False


# ===============================
# USER PROFILE ADMIN
# ===============================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileAdminForm

    list_display = (
        'account_label',
        'account_type_badge',
        'is_premium',
        'subscription_plan',
        'subscription_start',
        'subscription_expiry',
        'subscription_status',
        'lessons_used',
        'lesson_limit',
        'can_generate',
        'is_active',
    )

    search_fields = ('user__email', 'user__username', 'device_id')

    list_filter = (
        GuestFilter,
        'is_premium',
        'subscription_plan',
        'is_active',
    )

    actions = [activate_selected_premium, deactivate_selected_premium]

    # subscription_status is a callable — must be listed here
    # so Django treats it as a readonly method, not a model field
    readonly_fields = ('subscription_status', 'created_at', 'updated_at')

    fieldsets = (
        ('Identity', {
            'fields': ('user', 'device_id')
        }),
        ('Access Control', {
            'fields': (
                'is_active', 'is_premium', 'can_generate',
                'can_download_pdf', 'can_download_docx', 'can_copy_word'
            )
        }),
        ('Subscription', {
            'description': (
                '💡 Tip: Select a Plan + check Is Premium, then Save. '
                'Expiry and lesson limit are always recalculated automatically. '
                'Weekly = 5 days / 50 lessons | '
                'Monthly = 20 days / 200 lessons | '
                'Term = 60 days / 600 lessons.'
            ),
            'fields': (
                'subscription_plan',
                'subscription_start',
                'subscription_expiry',
                'subscription_status',
                'lesson_limit',
            )
        }),
        ('Usage', {
            'fields': ('lessons_used',)
        }),
        ('Prefill Data', {
            'classes': ('collapse',),
            'fields': (
                'school_name', 'teacher_name',
                'default_term', 'class_size', 'references'
            )
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )

    # ── Custom columns ─────────────────────────────────────────────────
    def account_label(self, obj):
        if obj.user:
            return obj.user.email or obj.user.username
        short = obj.device_id[:12] + '…' if obj.device_id else 'unknown'
        return f"Guest [{short}]"
    account_label.short_description = 'Account'

    def account_type_badge(self, obj):
        if obj.user:
            return mark_safe('<span style="color:#2e7d32;font-weight:700;">👤 User</span>')
        return mark_safe('<span style="color:#888;font-weight:700;">👻 Guest</span>')
    account_type_badge.short_description = 'Type'

    def subscription_status(self, obj):
        if obj.is_premium:
            if not obj.subscription_expiry:
                return mark_safe('<span style="color:#1565c0;font-weight:600;">⭐ Permanent</span>')
            if obj.subscription_expiry >= timezone.now():
                return mark_safe('<span style="color:#2e7d32;font-weight:600;">✅ Active</span>')
            return mark_safe('<span style="color:#c62828;font-weight:600;">❌ Expired</span>')
        return mark_safe('<span style="color:#888;">— Free</span>')
    subscription_status.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        """
        KEY FIX: Always recalculates expiry AND lesson_limit when plan is set.
        Removed all 'if not' guards — changing Monthly → Term now correctly
        overwrites the old 200 limit with 600, and recalculates expiry too.
        subscription_start is only set to now() if not already provided.
        """
        if obj.is_premium and obj.subscription_plan:
            if not obj.subscription_start:
                obj.subscription_start = timezone.now()
            # ✅ No 'if not' guard — always overwrites old values
            days = PLAN_DURATIONS.get(obj.subscription_plan, 5)
            obj.subscription_expiry = obj.subscription_start + timedelta(days=days)
            obj.lesson_limit = SUBSCRIPTION_LIMITS.get(obj.subscription_plan)

        super().save_model(request, obj, form, change)

    class Media:
        js = ('admin/js/jquery.init.js',)


# ===============================
# SUBSCRIPTION ADMIN
# ===============================
@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'plan', 'start_date', 'end_date', 'active')
    list_filter = ('plan', 'active')
    search_fields = ('user_profile__user__email',)


# ===============================
# TEACHING STRATEGY ADMIN
# ===============================
@admin.register(TeachingStrategy)
class TeachingStrategyAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'is_premium_only')
    list_filter = ('is_active', 'is_premium_only')
    search_fields = ('name',)


@admin.register(LessonStrategyStep)
class LessonStrategyStepAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'strategy', 'step_order', 'duration_minutes')
    list_filter = ('strategy', 'lesson')
    ordering = ('lesson', 'strategy', 'step_order')


# ===============================
# GENERATED LESSON PLAN ADMIN
# ===============================
@admin.register(GeneratedLessonPlan)
class GeneratedLessonPlanAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user_email',
        'subject',
        'lesson_title_short',
        'class_name',
        'term',
        'created_at',
    )
    list_filter = ('subject', 'term', 'created_at')
    search_fields = (
        'profile__user__email',
        'subject',
        'lesson_title',
        'unit_title',
    )
    readonly_fields = (
        'profile', 'subject', 'unit_title', 'lesson_title',
        'class_name', 'term', 'created_at', 'html_snapshot_preview'
    )
    ordering = ('-created_at',)

    fieldsets = (
        ('Plan Info', {
            'fields': (
                'profile', 'subject', 'unit_title',
                'lesson_title', 'class_name', 'term', 'created_at'
            )
        }),
        ('HTML Snapshot', {
            'classes': ('collapse',),
            'fields': ('html_snapshot_preview',)
        }),
    )

    def user_email(self, obj):
        if obj.profile and obj.profile.user:
            return obj.profile.user.email
        return '—'
    user_email.short_description = 'User'

    def lesson_title_short(self, obj):
        title = obj.lesson_title or ''
        return title[:60] + '…' if len(title) > 60 else title
    lesson_title_short.short_description = 'Lesson Title'

    def html_snapshot_preview(self, obj):
        if obj.html_snapshot:
            preview = obj.html_snapshot[:2000]
            suffix = '…' if len(obj.html_snapshot) > 2000 else ''
            return format_html(
                '<div style="max-height:400px;overflow:auto;'
                'border:1px solid #ddd;padding:10px;">{}{}</div>',
                preview, suffix
            )
        return mark_safe('—')
    html_snapshot_preview.short_description = 'HTML Preview'

# ADD THIS TO YOUR lessons/admin.py
# ─────────────────────────────────────────────────────────────────────────────

# from lessons.models import ManualPaymentProof, Subscription, UserProfile  ← your existing imports


@admin.register(ManualPaymentProof)
class ManualPaymentProofAdmin(admin.ModelAdmin):
    list_display  = ('full_name', 'phone', 'plan', 'tx_id', 'amount', 'status', 'submitted_at')
    list_filter   = ('status', 'plan')
    search_fields = ('full_name', 'tx_id', 'phone', 'user__email')
    readonly_fields = ('submitted_at', 'reviewed_at', 'user', 'screenshot_preview')
    ordering      = ('-submitted_at',)

    fieldsets = (
        ('Submitted Proof', {
            'fields': ('user', 'full_name', 'phone', 'plan', 'tx_id', 'amount', 'screenshot', 'screenshot_preview', 'submitted_at')
        }),
        ('Admin Decision', {
            'fields': ('status', 'admin_note', 'reviewed_at')
        }),
    )

    actions = ['approve_selected', 'reject_selected']

    def screenshot_preview(self, obj):
        from django.utils.html import format_html
        if obj.screenshot:
            return format_html('<img src="{}" style="max-height:200px;border-radius:8px;" />', obj.screenshot.url)
        return '—'
    screenshot_preview.short_description = 'Screenshot Preview'

    def approve_selected(self, request, queryset):
        """
        Bulk approve: marks proofs as approved and activates subscriptions.
        Extend this to actually create/extend Subscription objects as needed.
        """
        from lessons.models import Subscription  # adjust import to your actual model
        from datetime import timedelta

        plan_days = {'weekly': 7, 'monthly': 30, 'term': 90}
        count = 0

        for proof in queryset.filter(status='pending'):
            proof.status      = 'approved'
            proof.reviewed_at = timezone.now()
            proof.save()

            # Activate subscription if user is linked
            if proof.user:
                days = plan_days.get(proof.plan, 30)
                sub, created = Subscription.objects.get_or_create(user=proof.user)
                now = timezone.now()
                start = max(sub.end_date, now) if (not created and sub.end_date and sub.end_date > now) else now
                sub.plan       = proof.plan
                sub.start_date = start
                sub.end_date   = start + timedelta(days=days)
                sub.is_active  = True
                sub.save()
            count += 1

        self.message_user(request, f'✅ {count} proof(s) approved and subscriptions activated.')
    approve_selected.short_description = '✅ Approve selected & activate subscriptions'

    def reject_selected(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='rejected',
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'❌ {updated} proof(s) rejected.')
    reject_selected.short_description = '❌ Reject selected proofs'
