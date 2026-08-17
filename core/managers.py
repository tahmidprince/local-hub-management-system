"""
core/managers.py

Custom manager for the email-based `User` model. Kept separate from
models.py to avoid import-order issues and to keep the manager easily
testable/reusable.
"""
from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """
    Manager for a User model that uses email as the unique identifier
    instead of a username.
    """
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set.")
        if not extra_fields.get("full_name"):
            raise ValueError("The full_name field must be set.")
        if not extra_fields.get("phone_number"):
            raise ValueError("The phone_number field must be set.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", "seeker")
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)
