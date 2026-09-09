"""
core/admin.py

Django admin configuration for the full LocalHub schema:
Part 1 — User, Profile
Part 2 — WorkEntry / TaskProposal (posting), CreativeItem / CartItem /
         Order / OrderItem (shop), Payment (escrow / finance).
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    CartItem,
    CreativeItem,
    Order,
    OrderItem,
    Payment,
    Profile,
    TaskProposal,
    User,
    WorkEntry,
)

# =====================================================================
# PART 1 — AUTH
# =====================================================================


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["-date_joined"]
    list_display = ["email", "full_name", "role", "is_verified", "wallet_balance", "is_staff", "is_active"]
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
    list_filter = ["rating"]
    search_fields = ["user__email", "user__full_name"]


# =====================================================================
# PART 2 — TASK POSTING & BIDDING
# =====================================================================


class TaskProposalInline(admin.TabularInline):
    model = TaskProposal
    extra = 0
    fields = ["provider", "proposed_bid", "est_delivery_days", "status", "created_at"]
    readonly_fields = ["created_at"]
    autocomplete_fields = ["provider"]


@admin.register(WorkEntry)
class WorkEntryAdmin(admin.ModelAdmin):
    list_display = [
        "title", "seeker", "provider", "category", "sub_category",
        "budget", "status", "created_at",
    ]
    list_filter = ["status", "category", "created_at"]
    search_fields = [
        "title", "sub_category", "description", "location",
        "seeker__email", "seeker__full_name",
        "provider__email", "provider__full_name",
    ]
    autocomplete_fields = ["seeker", "provider"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"
    inlines = [TaskProposalInline]


@admin.register(TaskProposal)
class TaskProposalAdmin(admin.ModelAdmin):
    list_display = ["task", "provider", "proposed_bid", "est_delivery_days", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["task__title", "provider__email", "provider__full_name", "cover_letter"]
    autocomplete_fields = ["task", "provider"]
    readonly_fields = ["created_at"]


# =====================================================================
# PART 2 — CREATIVE SHOP
# =====================================================================


@admin.register(CreativeItem)
class CreativeItemAdmin(admin.ModelAdmin):
    list_display = ["item_name", "artist", "price", "stock_quantity", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["item_name", "description", "artist__email", "artist__full_name"]
    autocomplete_fields = ["artist"]
    readonly_fields = ["created_at"]
    list_editable = ["is_active", "stock_quantity"]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["user", "item", "quantity", "line_total"]
    list_filter = ["item"]
    search_fields = ["user__email", "user__full_name", "item__item_name"]
    autocomplete_fields = ["user", "item"]

    @admin.display(description="Line total")
    def line_total(self, obj):
        return obj.line_total


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ["item", "quantity", "unit_price", "subtotal"]
    readonly_fields = ["subtotal"]
    autocomplete_fields = ["item"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "buyer", "total_amount", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["buyer__email", "buyer__full_name", "shipping_address"]
    autocomplete_fields = ["buyer"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["order", "item", "quantity", "unit_price", "subtotal"]
    search_fields = ["order__id", "item__item_name"]
    autocomplete_fields = ["order", "item"]


# =====================================================================
# PART 2 — FINANCIAL / ESCROW
# =====================================================================


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "transaction_id", "payer", "recipient", "amount",
        "payment_method", "status", "task", "order", "created_at",
    ]
    list_filter = ["status", "payment_method", "created_at"]
    search_fields = [
        "transaction_id", "payer__email", "payer__full_name",
        "recipient__email", "recipient__full_name",
    ]
    autocomplete_fields = ["payer", "recipient", "task", "order"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"
