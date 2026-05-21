from django.contrib import admin
from .models import Plan, Task, UserPlan, UserTask, SystemSettings

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "reward", "media_type", "active", "created_at")
    list_filter = ("active", "media_type")
    search_fields = ("title", "description")

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("plan_level", "title", "amount", "reward_multiplier", "daily_earning_limit", "active")
    list_filter = ("active", "plan_level")
    search_fields = ("title", "description")

@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ("user", "task", "completed_at")
    search_fields = ("user__email", "task__title")
    list_select_related = ("user", "task")

@admin.register(UserPlan)
class UserPlanAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "joined_at")
    search_fields = ("user__email", "plan__title")
    list_select_related = ("user", "plan")

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ("telegram_link", "whatsapp_link", "support_phone", "support_email", "updated_at")
    fieldsets = (
        ("Communication Links", {
            "fields": ("telegram_link", "whatsapp_link", "support_phone", "support_email")
        }),
        ("Social Media Links", {
            "fields": ("facebook_link", "instagram_link")
        }),
        ("Announcement", {
            "fields": ("announcement_banner",)
        }),
    )

    def has_add_permission(self, request):
        """Prevent adding multiple instances"""
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of the settings instance"""
        return False
