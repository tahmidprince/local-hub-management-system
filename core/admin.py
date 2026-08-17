from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Profile, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["-date_joined"]
    list_display = ["email", "full_name", "role", "is_verified", "is_staff", "is_active"]
    list_filter = ["role", "is_verified", "is_staff", "is_active"]
    search_fields = ["email", "full_name", "phone_number"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("full_name", "phone_number", "role", "wallet_balance")}),
        ("Status", {"fields": ("is_verified", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "phone_number", "role", "password1", "password2"),
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "rating"]
    search_fields = ["user__email", "user__full_name"]
