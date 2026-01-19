from django.contrib import admin
from .models import (
    Level,
    Class,
    Subject,
    Unit,
    Lesson,
    UserProfile,
    Subscription
)

# -----------------------------
# INLINE MODELS
# -----------------------------
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


# -----------------------------
# MODEL ADMINS
# -----------------------------
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


# -----------------------------
# USER PROFILE / SUBSCRIPTION
# -----------------------------
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'device_id',
        'free_plans_used',
        'premium_active',
        'premium_start',
        'premium_expiry'
    )
    search_fields = ('user__email', 'device_id')
    list_filter = ('premium_active',)


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
