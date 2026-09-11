"""
core/models.py

LocalHub Management System — full schema.

Part 1 (existing): custom auth — User, Profile
Part 2 (new):       task posting & bidding, the Creative Shop, and the
                     financial / escrow layer that ties tasks and
                     orders to payments.
"""
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models

from .managers import UserManager

# =====================================================================
# PART 1 — AUTH
# =====================================================================


class User(AbstractUser):
    """
    Email-based custom user model with a role field driving access
    control across seeker / provider / artist / admin dashboards.
    """

    class Role(models.TextChoices):
        SEEKER = "seeker", "Seeker"
        PROVIDER = "provider", "Provider"
        ARTIST = "artist", "Artist"
        ADMIN = "admin", "Admin"

    username = None
    email = models.EmailField("email address", unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.SEEKER)
    is_verified = models.BooleanField(default=False)
    wallet_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "phone_number"]

    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    @property
    def is_seeker(self):
        return self.role == self.Role.SEEKER

    @property
    def is_provider(self):
        return self.role == self.Role.PROVIDER

    @property
    def is_artist(self):
        return self.role == self.Role.ARTIST

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN


class Profile(models.Model):
    """
    Extended, editable profile data kept separate from the auth-critical
    User model. Auto-created via a post_save signal (see signals.py).
    """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    bio = models.TextField(blank=True)
    skills = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(
        upload_to="profiles/", default="profiles/default.png"
    )
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def __str__(self):
        return f"Profile: {self.user.full_name}"


# =====================================================================
# PART 2 — TASK POSTING & BIDDING ("The Posting" side)
# =====================================================================


class WorkEntry(models.Model):
    """
    A task/job posted by a seeker, optionally assigned to a provider
    once a TaskProposal is accepted.
    """

    class Category(models.TextChoices):
        DAILY_LABOR = "daily_labor", "Daily Labor"
        ONLINE_TECH = "online_tech", "Online / Tech"

    class Status(models.TextChoices):
        POSTED = "posted", "Posted"
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    seeker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posted_tasks",
        limit_choices_to={"role": User.Role.SEEKER},
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
        limit_choices_to={"role": User.Role.PROVIDER},
    )

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=Category.choices)
    sub_category = models.CharField(
        max_length=100, help_text="e.g. Plumbing, Web Development, Tutoring"
    )
    budget = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    description = models.TextField()
    location = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.POSTED
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Work Entry"
        verbose_name_plural = "Work Entries"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["category", "sub_category"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class TaskProposal(models.Model):
    """
    A provider's bid on a posted WorkEntry.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

    task = models.ForeignKey(
        WorkEntry, on_delete=models.CASCADE, related_name="proposals"
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="proposals",
        limit_choices_to={"role": User.Role.PROVIDER},
    )
    proposed_bid = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    est_delivery_days = models.PositiveIntegerField()
    cover_letter = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Task Proposal"
        verbose_name_plural = "Task Proposals"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["task", "provider"], name="unique_proposal_per_provider_task"
            )
        ]

    def __str__(self):
        return f"Bid by {self.provider} on {self.task} — {self.proposed_bid}"


# =====================================================================
# PART 2 — THE CREATIVE SHOP
# =====================================================================


class CreativeItem(models.Model):
    """
    A product listed for sale by an artist in the Creative Shop.
    """
    artist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="artworks",
        limit_choices_to={"role": User.Role.ARTIST},
    )
    item_name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    stock_quantity = models.PositiveIntegerField(default=1)
    image = models.ImageField(upload_to="shop/")
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(
        default=False,
        help_text="Must be approved by an admin before it appears in the public shop catalog.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Creative Item"
        verbose_name_plural = "Creative Items"
        ordering = ["-created_at"]

    def __str__(self):
        return self.item_name

    @property
    def in_stock(self):
        return self.stock_quantity > 0


class CartItem(models.Model):
    """
    A single line in a user's shopping cart. One row per (user, item)
    pair — quantity tracks how many of that item they intend to buy.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_items"
    )
    item = models.ForeignKey(CreativeItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "item"], name="unique_cart_line_per_user_item"
            )
        ]

    def __str__(self):
        return f"{self.quantity} x {self.item.item_name} ({self.user})"

    @property
    def line_total(self):
        return self.quantity * self.item.price


class Order(models.Model):
    """
    A checked-out cart. Line items are captured in OrderItem so price
    history survives future CreativeItem edits.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PAID = "paid", "Paid"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    shipping_address = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} — {self.buyer} ({self.get_status_display()})"


class OrderItem(models.Model):
    """
    A frozen line item inside an Order — unit_price/subtotal are copied
    at checkout time so they don't drift if CreativeItem.price changes
    later. item uses PROTECT: a CreativeItem can't be hard-deleted while
    it's referenced by historical order records.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(CreativeItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity} x {self.item.item_name} (Order #{self.order_id})"

    def save(self, *args, **kwargs):
        # Keep subtotal consistent even if a caller forgets to set it.
        if self.unit_price is not None and self.quantity is not None:
            self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)


# =====================================================================
# PART 2 — FINANCIAL / ESCROW LAYER
# =====================================================================


class Payment(models.Model):
    """
    A single money movement in the system. Can back either a WorkEntry
    (escrowed until task completion) or a shop Order (captured on
    checkout) — task/order are mutually-optional FKs so one Payment
    model covers both flows.
    """

    class Method(models.TextChoices):
        WALLET = "wallet", "Wallet"
        COD = "cod", "Cash on Delivery"
        SSLZ = "sslz", "SSLCommerz"
        BANK = "bank", "Bank Account"
        BKASH = "bkash", "bKash"
        NAGAD = "nagad", "Nagad"
        CARD = "card", "Card"

    class Status(models.TextChoices):
        HELD_IN_ESCROW = "held_in_escrow", "Held in Escrow"
        RELEASED = "released", "Released"
        REFUNDED = "refunded", "Refunded"
        COMPLETED = "completed", "Completed"

    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments_made",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments_received",
    )
    task = models.ForeignKey(
        WorkEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    payment_method = models.CharField(max_length=20, choices=Method.choices)
    transaction_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.HELD_IN_ESCROW
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(task__isnull=False) | models.Q(order__isnull=False),
                name="payment_must_reference_task_or_order",
            )
        ]

    def __str__(self):
        return f"{self.transaction_id} — {self.amount} ({self.get_status_display()})"


class WithdrawalRequest(models.Model):
    """
    A user's request to cash out their `User.wallet_balance` to an
    external account (Bkash/Nagad/Bank). Submitting a request does NOT
    move money by itself — an admin reviews it and marks it
    completed/rejected, at which point the wallet debit (or refusal)
    actually happens.
    """

    class Method(models.TextChoices):
        BKASH = "bkash", "Bkash"
        NAGAD = "nagad", "Nagad"
        BANK = "bank", "Bank"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="withdrawal_requests",
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    method = models.CharField(max_length=20, choices=Method.choices)
    account_details = models.CharField(
        max_length=100,
        help_text="Bkash/Nagad phone number, or bank account number.",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Withdrawal Request"
        verbose_name_plural = "Withdrawal Requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — \u09f3{self.amount} ({self.get_status_display()})"
