"""
core/models.py

Custom user model (email-based auth, role-based access) and its
associated Profile model for the LocalHub Management System.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


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
