"""
core/forms.py

Part 1: registration / login forms.
Part 3: ModelForms that let Seekers post tasks and Artists list shop
        items directly from their dashboards.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import CreativeItem, TaskProposal, WorkEntry

User = get_user_model()


# =====================================================================
# PART 1 — AUTH FORMS
# =====================================================================


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        ),
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirm Password"}
        ),
    )

    class Meta:
        model = User
        fields = ["email", "full_name", "phone_number", "role"]
        widgets = {
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email address"}
            ),
            "full_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Full Name"}
            ),
            "phone_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Phone Number"}
            ),
            "role": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email", "").lower().strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number", "").strip()
        if User.objects.filter(phone_number=phone).exists():
            raise ValidationError("A user with this phone number already exists.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and len(password) < 8:
            self.add_error("password", "Password must be at least 8 characters long.")
        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email address",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        ),
    )

    error_messages = {
        "invalid_login": "Please enter a correct email and password.",
        "inactive": "This account is inactive.",
    }


# =====================================================================
# PART 3 — SEEKER / ARTIST DASHBOARD FORMS
# =====================================================================


class WorkEntryForm(forms.ModelForm):
    """
    Seeker-facing "post a task" form. `seeker`, `provider`, `status`,
    `created_at`, `updated_at` are all set/managed server-side, never
    by the client.
    """

    class Meta:
        model = WorkEntry
        exclude = ["seeker", "provider", "status", "created_at", "updated_at"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control", "placeholder": "e.g. Fix leaking kitchen sink"
            }),
            "category": forms.Select(attrs={"class": "form-select"}),
            "sub_category": forms.TextInput(attrs={
                "class": "form-control", "placeholder": "e.g. Plumbing, Web Development"
            }),
            "budget": forms.NumberInput(attrs={
                "class": "form-control", "placeholder": "0.00", "step": "0.01", "min": "0"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control", "rows": 4,
                "placeholder": "Describe what you need done, timeline, and any specifics."
            }),
            "location": forms.TextInput(attrs={
                "class": "form-control", "placeholder": "e.g. Gulshan, Dhaka"
            }),
        }

    def clean_budget(self):
        budget = self.cleaned_data.get("budget")
        if budget is not None and budget <= 0:
            raise ValidationError("Budget must be greater than zero.")
        return budget


class CreativeItemForm(forms.ModelForm):
    """
    Artist-facing "add shop item" form. `artist`, `is_active`, and
    `created_at` are all set/managed server-side.
    """

    class Meta:
        model = CreativeItem
        exclude = ["artist", "is_active", "created_at"]
        widgets = {
            "item_name": forms.TextInput(attrs={
                "class": "form-control", "placeholder": "e.g. Hand-painted ceramic mug"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control", "rows": 3,
                "placeholder": "Describe the item, materials, dimensions, etc."
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control", "placeholder": "0.00", "step": "0.01", "min": "0"
            }),
            "stock_quantity": forms.NumberInput(attrs={
                "class": "form-control", "min": "0"
            }),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price <= 0:
            raise ValidationError("Price must be greater than zero.")
        return price


class TaskProposalForm(forms.ModelForm):
    """
    Provider-facing "bid on a task" form. `task`, `provider`, `status`,
    and `created_at` are all set/managed server-side — the provider
    only supplies their bid amount, timeline, and pitch.
    """

    class Meta:
        model = TaskProposal
        exclude = ["task", "provider", "status", "created_at"]
        widgets = {
            "proposed_bid": forms.NumberInput(attrs={
                "class": "form-control", "placeholder": "0.00", "step": "0.01", "min": "0"
            }),
            "est_delivery_days": forms.NumberInput(attrs={
                "class": "form-control", "placeholder": "e.g. 3", "min": "1"
            }),
            "cover_letter": forms.Textarea(attrs={
                "class": "form-control", "rows": 4,
                "placeholder": "Introduce yourself and explain why you're a good fit for this task."
            }),
        }

    def clean_proposed_bid(self):
        proposed_bid = self.cleaned_data.get("proposed_bid")
        if proposed_bid is not None and proposed_bid <= 0:
            raise ValidationError("Your bid must be greater than zero.")
        return proposed_bid
