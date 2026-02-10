# File: /lesson-plan-generator/backend/lessons/admin.py

from datetime import timedelta
from django.utils import timezone
from django.contrib import admin
from django import forms
from .models import (
    Level,
    Class,
    Subject,
    Unit,
    Lesson,
    UserProfile,
    Subscription
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
        'title',
        'number',
        'unit',
        'subject_name',
        'class_name',
        'level_name',
        'is_premium'
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
@admin.action(description="Activate selected users for premium (default weekly)")
def activate_selected_premium(modeladmin, request, queryset):
    """
    Bulk admin action: Activate premium for selected users.
    Uses default weekly plan (7 days) unless subscription_plan set on profile.
    Resets lessons_used.
    """
    plan_durations = {'weekly': 7, 'monthly': 30, 'term': 90}
    activated_count = 0

    for profile in queryset:
        # Determine duration: use plan on profile if available
        days = plan_durations.get(profile.subscription_plan, 7)
        profile.activate_premium(days=days, plan=profile.subscription_plan or "weekly")
        profile.lessons_used = 0
        profile.save()
        activated_count += 1
        print(f"[Admin Bulk] Premium activated for {profile}, expires {profile.subscription_expiry}")

    modeladmin.message_user(request, f"✅ Activated premium for {activated_count} users.")


# ===============================
# USER PROFILE FORM (Admin)
# ===============================
class UserProfileAdminForm(forms.ModelForm):
    custom_premium_days = forms.IntegerField(
        required=False,
        min_value=1,
        label="Custom Premium Duration (days)",
        help_text="Optional: Override plan duration for premium access."
    )

    class Meta:
        model = UserProfile
        fields = '__all__'


# ===============================
# USER PROFILE ADMIN
# ===============================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileAdminForm
    list_display = (
        'user',
        'device_id',
        'is_premium',
        'subscription_plan',
        'subscription_start',
        'subscription_expiry',
        'subscription_status',
        'lessons_used',
        'lesson_limit',
        'can_generate'
    )
    search_fields = ('user__email', 'device_id')
    list_filter = ('is_premium', 'subscription_plan', 'is_active')
    actions = [activate_selected_premium]
    readonly_fields = ('subscription_status',)

    def subscription_status(self, obj):
        if obj.is_premium and obj.subscription_expiry:
            return "Active" if obj.subscription_expiry >= timezone.now() else "Expired"
        return "Inactive"
    subscription_status.short_description = "Status"
    
    def save_model(self, request, obj, form, change):
       """
       Admin is authoritative.
       Do NOT auto-activate premium unless admin explicitly does it.
       """
       super().save_model(request, obj, form, change)


# ===============================
# SUBSCRIPTION ADMIN
# ===============================
@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user_profile',
        'plan',
        'start_date',
        'end_date',
        'active'
    )
    list_filter = ('plan', 'active')
    search_fields = ('user_profile__user__email',)
