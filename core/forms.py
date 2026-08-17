"""
core/forms.py

Registration and login forms. Uses get_user_model() rather than
importing User directly, per the "avoid tight coupling / circular
import" constraint.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

User = get_user_model()


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
    """
    AuthenticationForm swaps `username` -> email under the hood because
    USERNAME_FIELD = 'email' on the custom User model; we just relabel
    and re-style the field for the template.
    """
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
