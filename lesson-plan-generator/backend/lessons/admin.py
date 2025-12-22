
from django.contrib import admin
from .models import Level, Class, Subject, Unit, Lesson, DeviceAccess

# -----------------------------
# Existing Models
# -----------------------------
admin.site.register(Level)
admin.site.register(Class)
admin.site.register(Subject)
admin.site.register(Unit)
admin.site.register(Lesson)

# -----------------------------
# Device Access Model
# -----------------------------
@admin.register(DeviceAccess)
class DeviceAccessAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'free_plans_used', 'premium_active', 'premium_start', 'premium_expiry')
    list_filter = ('premium_active',)
    search_fields = ('device_id',)
