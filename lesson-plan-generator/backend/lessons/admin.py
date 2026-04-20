# File: /lesson-plan-generator/backend/lessons/admin.py

from datetime import timedelta
from django.utils import timezone
from django.contrib import admin
from django import forms
from django.utils.html import format_html, mark_safe
import csv
from django.http import HttpResponse

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
    ChatHistory,
    Interaction,
    BotConfig,
    BotResponse,
    QuickReply,
    TopBanner,
    HeroBanner,
    BottomAd,
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

    force_reset = forms.BooleanField(
        required=False,
        initial=False,
        label="🔄 Reset subscription from selected plan",
        help_text=(
            "✅ CHECK THIS to recalculate start date, expiry, lesson limit "
            "and reset lessons used to 0 based on the selected plan. "
            "❌ LEAVE UNCHECKED to manually edit lesson_limit / lessons_used freely."
        )
    )

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
                '💡 TWO MODES: '
                '① RESET MODE — check Is Premium + select plan + check 🔄 Reset → Save. '
                'Auto-sets dates, limit and clears usage. '
                '② MANUAL MODE — uncheck 🔄 Reset, edit lesson_limit / lessons_used freely → Save. '
                'Weekly = 5 days / 50 lessons | '
                'Monthly = 20 days / 200 lessons | '
                'Term = 60 days / 600 lessons.'
            ),
            'fields': (
                'subscription_plan',
                'force_reset',
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
        from django.contrib import messages

        if obj.is_premium and not obj.subscription_plan:
            messages.error(
                request,
                "❌ Please select a subscription plan before activating premium."
            )
            return

        if obj.is_premium and obj.subscription_plan:
            force_reset = form.cleaned_data.get('force_reset', False)
            original    = UserProfile.objects.filter(pk=obj.pk).first()
            first_time  = (
                original is None or
                not original.is_premium or
                not original.subscription_expiry
            )

            if force_reset or first_time:
                obj.subscription_start  = timezone.now()
                days = PLAN_DURATIONS.get(obj.subscription_plan, 5)
                obj.subscription_expiry = obj.subscription_start + timedelta(days=days)
                obj.lesson_limit        = SUBSCRIPTION_LIMITS.get(obj.subscription_plan)
                obj.lessons_used        = 0

                messages.success(
                    request,
                    f"✅ Subscription reset: {obj.subscription_plan.capitalize()} plan. "
                    f"Limit = {obj.lesson_limit} lessons, "
                    f"Expires = {obj.subscription_expiry.strftime('%d %b %Y')}."
                )
            else:
                messages.info(
                    request,
                    f"💾 Manual save: lesson_limit={obj.lesson_limit}, "
                    f"lessons_used={obj.lessons_used} kept as entered."
                )

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


# ===============================
# MANUAL PAYMENT PROOF ADMIN
# ===============================
@admin.register(ManualPaymentProof)
class ManualPaymentProofAdmin(admin.ModelAdmin):
    list_display    = ('full_name', 'phone', 'plan', 'tx_id', 'amount', 'status', 'submitted_at')
    list_filter     = ('status', 'plan')
    search_fields   = ('full_name', 'tx_id', 'phone', 'user__email')
    readonly_fields = ('submitted_at', 'reviewed_at', 'user', 'screenshot_preview')
    ordering        = ('-submitted_at',)

    fieldsets = (
        ('Submitted Proof', {
            'fields': (
                'user', 'full_name', 'phone', 'plan',
                'tx_id', 'amount', 'screenshot', 'screenshot_preview', 'submitted_at'
            )
        }),
        ('Admin Decision', {
            'fields': ('status', 'admin_note', 'reviewed_at')
        }),
    )

    actions = ['approve_selected', 'reject_selected']

    def screenshot_preview(self, obj):
        if obj.screenshot:
            return format_html(
                '<img src="{}" style="max-height:200px;border-radius:8px;" />',
                obj.screenshot.url
            )
        return '—'
    screenshot_preview.short_description = 'Screenshot Preview'

    def approve_selected(self, request, queryset):
        plan_days = {'weekly': 7, 'monthly': 30, 'term': 90}
        count = 0

        for proof in queryset.filter(status='pending'):
            proof.status      = 'approved'
            proof.reviewed_at = timezone.now()
            proof.save()

            if not proof.user:
                continue

            profile, _ = UserProfile.objects.get_or_create(user=proof.user)
            profile.activate_premium(plan=proof.plan, reset_usage=True)

            days     = plan_days.get(proof.plan, 30)
            end_date = timezone.now() + timedelta(days=days)

            Subscription.objects.create(
                user_profile = profile,
                plan         = proof.plan,
                end_date     = end_date,
                active       = True,
            )
            count += 1

        self.message_user(request, f'✅ {count} proof(s) approved and subscriptions activated.')
    approve_selected.short_description = '✅ Approve selected & activate subscriptions'

    def reject_selected(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status      = 'rejected',
            reviewed_at = timezone.now()
        )
        self.message_user(request, f'❌ {updated} proof(s) rejected.')
    reject_selected.short_description = '❌ Reject selected proofs'


# ===============================
# CHAT HISTORY ADMIN
# ===============================
@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'intent', 'message_preview', 'direction', 'created_at']
    list_filter  = ['intent', 'direction', 'created_at']
    search_fields = ['message', 'user__username', 'user__email']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    actions = ['export_chat_history_csv']

    fieldsets = (
        ('User Info', {
            'fields': ('user', 'conversation_id', 'direction')
        }),
        ('Message', {
            'fields': ('message', 'intent'),
            'classes': ('wide',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'

    def export_chat_history_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="chat_history.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'User', 'Intent', 'Direction', 'Message'])
        for chat in queryset:
            writer.writerow([
                chat.created_at,
                chat.user.username if chat.user else 'Anonymous',
                chat.intent or 'N/A',
                chat.direction,
                chat.message,
            ])
        return response
    export_chat_history_csv.short_description = 'Export selected chats to CSV'


# ===============================
# INTERACTION ADMIN
# ===============================
@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display  = ['id', 'user', 'intent', 'user_message_preview', 'satisfied', 'timestamp']
    list_filter   = ['intent', 'satisfied', 'timestamp']
    search_fields = ['user_message', 'bot_response', 'user__username', 'user__email']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    actions = ['export_interactions_csv']

    fieldsets = (
        ('User Info', {
            'fields': ('user',)
        }),
        ('Conversation', {
            'fields': ('intent', 'user_message', 'bot_response', 'satisfied'),
            'classes': ('wide',)
        }),
        ('Metadata', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )

    def user_message_preview(self, obj):
        return obj.user_message[:50] + '...' if len(obj.user_message) > 50 else obj.user_message
    user_message_preview.short_description = 'User Message'

    def export_interactions_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="interactions.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'User', 'Intent', 'User Message', 'Bot Response', 'Satisfied'])
        for interaction in queryset:
            writer.writerow([
                interaction.timestamp,
                interaction.user.username if interaction.user else 'Anonymous',
                interaction.intent,
                interaction.user_message,
                interaction.bot_response,
                interaction.satisfied or 'N/A',
            ])
        return response
    export_interactions_csv.short_description = 'Export selected interactions to CSV'


# ===============================
# BOT CONFIG ADMIN
# ===============================
@admin.register(BotConfig)
class BotConfigAdmin(admin.ModelAdmin):
    list_display  = ['key', 'value_preview', 'updated_at']
    search_fields = ['key', 'value']

    fieldsets = (
        ('Configuration', {
            'fields': ('key', 'value'),
            'classes': ('wide',)
        }),
    )

    def value_preview(self, obj):
        return obj.value[:50] + '...' if len(obj.value) > 50 else obj.value
    value_preview.short_description = 'Value'


# ===============================
# BOT RESPONSE ADMIN
# ===============================
@admin.register(BotResponse)
class BotResponseAdmin(admin.ModelAdmin):
    list_display  = ['intent', 'is_active', 'priority', 'response_preview', 'updated_at']
    list_editable = ['is_active', 'priority']
    list_filter   = ['is_active', 'priority']
    search_fields = ['intent', 'response_template']

    fieldsets = (
        ('Intent Settings', {
            'fields': ('intent', 'is_active', 'priority')
        }),
        ('Response Content', {
            'fields': ('response_template',),
            'classes': ('wide',),
            'description': 'Use variables: {username}, {remaining}, {email}, {plan}'
        }),
    )

    def response_preview(self, obj):
        return obj.response_template[:50] + '...' if len(obj.response_template) > 50 else obj.response_template
    response_preview.short_description = 'Response'


# ===============================
# QUICK REPLY ADMIN
# ===============================
@admin.register(QuickReply)
class QuickReplyAdmin(admin.ModelAdmin):
    list_display  = ['icon', 'text', 'message_preview', 'row', 'order', 'is_active']
    list_editable = ['row', 'order', 'is_active']
    list_filter   = ['row', 'is_active']
    search_fields = ['text', 'message']

    fieldsets = (
        ('Button Display', {
            'fields': ('text', 'icon', 'row', 'order')
        }),
        ('Action', {
            'fields': ('message', 'is_active'),
            'description': 'This message will be sent to the bot when button is clicked'
        }),
    )

    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message sent'


# ===============================
# TOP BANNER ADMIN
# ===============================
@admin.register(TopBanner)
class TopBannerAdmin(admin.ModelAdmin):
    list_display  = (
        'text_preview', 'icon', 'badge', 'scroll_speed_display',
        'show_on_landing', 'show_on_index', 'order', 'active'
    )
    list_editable = ('order', 'active', 'show_on_landing', 'show_on_index')
    list_filter   = ('active', 'show_on_landing', 'show_on_index', 'show_on_pricing')
    search_fields = ('text',)
    ordering      = ('order',)
    fieldsets = (
        ('Content', {
            'fields': ('text', 'url', 'icon', 'badge', 'badge_color', 'color', 'bg')
        }),
        ('Speed & Display', {
            'fields': ('scroll_speed',),
            'description': (
                '⚡ Scroll speed controls how fast the ticker moves. '
                '10 = very fast | 44 = default | 120 = very slow. '
                "The first active banner's speed is used for all banners."
            )
        }),
        ('Template Targeting — which pages to show on', {
            'fields': ('show_on_landing', 'show_on_index', 'show_on_pricing')
        }),
        ('Ordering', {
            'fields': ('order', 'active')
        }),
    )

    def text_preview(self, obj):
        return obj.text[:70] + ('…' if len(obj.text) > 70 else '')
    text_preview.short_description = 'Announcement Text'

    def scroll_speed_display(self, obj):
        label = 'fast' if obj.scroll_speed < 25 else ('slow' if obj.scroll_speed > 70 else 'medium')
        return f"{obj.scroll_speed}s ({label})"
    scroll_speed_display.short_description = 'Speed'


# ===============================
# HERO BANNER ADMIN
# ===============================
@admin.register(HeroBanner)
class HeroBannerAdmin(admin.ModelAdmin):
    list_display  = (
        'headline_preview', 'badge', 'duration_display',
        'show_on_landing', 'show_on_index', 'order', 'active', 'image_thumb'
    )
    list_editable = ('order', 'active', 'show_on_landing', 'show_on_index')
    list_filter   = ('active', 'show_on_landing', 'show_on_index', 'show_on_pricing')
    search_fields = ('headline', 'description')
    ordering      = ('order',)
    fieldsets = (
        ('Content', {
            'fields': ('headline', 'description', 'cta_text', 'cta_url', 'image')
        }),
        ('Style', {
            'fields': ('badge', 'badge_color', 'bg_color', 'bg_color2'),
            'description': (
                'bg_color = left/dark side.  bg_color2 = right/light side.  '
                'Example: dark blue #0d1b2a → teal #1a5c6b for ocean feel.  '
                'Or deep green #0d3a1a → lime #2a6b1a for nature feel.'
            )
        }),
        ('Timing', {
            'fields': ('duration',),
            'description': (
                '⏱ How many seconds this slide stays before auto-advancing.  '
                '5 = snappy | 8 = default | 15 = slower | 30 = very slow.'
            )
        }),
        ('Template Targeting — which pages to show on', {
            'fields': ('show_on_landing', 'show_on_index', 'show_on_pricing')
        }),
        ('Ordering', {
            'fields': ('order', 'active')
        }),
    )

    def headline_preview(self, obj):
        return obj.headline[:60] + ('…' if len(obj.headline) > 60 else '')
    headline_preview.short_description = 'Headline'

    def duration_display(self, obj):
        return f"{obj.duration}s"
    duration_display.short_description = 'Duration'

    def image_thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:36px;border-radius:4px;">',
                obj.image.url
            )
        return '—'
    image_thumb.short_description = 'Image'


# ===============================
# BOTTOM AD ADMIN
# ===============================
@admin.register(BottomAd)
class BottomAdAdmin(admin.ModelAdmin):
    list_display  = (
        'title', 'subtitle_preview', 'badge',
        'show_on_landing', 'show_on_index', 'order', 'active', 'image_thumb'
    )
    list_editable = ('order', 'active', 'show_on_landing', 'show_on_index')
    list_filter   = ('active', 'show_on_landing', 'show_on_index', 'show_on_pricing')
    search_fields = ('title', 'subtitle')
    ordering      = ('order',)
    fieldsets = (
        ('Content', {
            'fields': ('title', 'subtitle', 'image', 'url')
        }),
        ('Style', {
            'fields': ('badge', 'badge_color')
        }),
        ('Template Targeting — which pages to show on', {
            'fields': ('show_on_landing', 'show_on_index', 'show_on_pricing')
        }),
        ('Ordering', {
            'fields': ('order', 'active')
        }),
    )

    def subtitle_preview(self, obj):
        return obj.subtitle[:50] + ('…' if len(obj.subtitle) > 50 else '')
    subtitle_preview.short_description = 'Subtitle'

    def image_thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:36px;border-radius:4px;">',
                obj.image.url
            )
        return '—'
    image_thumb.short_description = 'Image'