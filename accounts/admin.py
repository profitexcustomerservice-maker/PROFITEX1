from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import messages
from .models import User, SocialLink

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "first_name", "last_name", "current_plan_level", "is_admin", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("is_active", "is_staff", "is_admin", "current_plan_level")
    readonly_fields = ("last_active", "last_rewarded_at", "created_at")
    ordering = ("-created_at", "email")
    fieldsets = (
        (None, {"fields": ("email", "password")} ),
        ("Personal info", {"fields": ("first_name", "last_name", "current_plan_level")} ),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_admin", "is_superuser", "groups", "user_permissions")} ),
        ("Activity", {"fields": ("created_at", "last_active", "last_rewarded_at")} ),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "first_name", "last_name", "is_staff", "is_active"),
        }),
    )
    filter_horizontal = ("groups", "user_permissions")
    actions = ["block_users", "unblock_users", "make_admin", "remove_admin"]

    def block_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} user(s) blocked successfully.", messages.SUCCESS)
    block_users.short_description = "Block selected users"

    def unblock_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} user(s) unblocked successfully.", messages.SUCCESS)
    unblock_users.short_description = "Unblock selected users"

    def make_admin(self, request, queryset):
        updated = queryset.update(is_admin=True, is_staff=True)
        self.message_user(request, f"{updated} user(s) made admin successfully.", messages.SUCCESS)
    make_admin.short_description = "Make selected users admin"

    def remove_admin(self, request, queryset):
        updated = queryset.update(is_admin=False, is_staff=False)
        self.message_user(request, f"{updated} user(s) removed from admin successfully.", messages.SUCCESS)
    remove_admin.short_description = "Remove admin from selected users"


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "icon", "is_active", "order", "created_at")
    list_filter = ("is_active", "created_at")
    list_editable = ("is_active", "order")
    search_fields = ("name", "url")
    ordering = ("order", "name")
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        (None, {
            "fields": ("name", "url", "icon", "is_active", "order")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
