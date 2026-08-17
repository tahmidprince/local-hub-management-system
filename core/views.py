"""
core/views.py

Auth flow (register / login / logout), a post-login role dispatcher,
and placeholder per-role dashboards.
"""
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .decorators import role_required
from .forms import UserLoginForm, UserRegistrationForm

ROLE_DASHBOARD_URLS = {
    "seeker": "dashboard_seeker",
    "provider": "dashboard_provider",
    "artist": "dashboard_artist",
    "admin": "dashboard_admin",
}


def register_view(request):
    if request.user.is_authenticated:
        return redirect("role_dispatch")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully. Welcome!")
            return redirect("role_dispatch")
    else:
        form = UserRegistrationForm()

    return render(request, "auth/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("role_dispatch")

    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.full_name}.")
                return redirect("role_dispatch")
            messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = UserLoginForm()

    return render(request, "auth/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")


@login_required
def role_dispatch_view(request):
    """
    Sends a freshly authenticated user to the dashboard that matches
    their role.
    """
    target = ROLE_DASHBOARD_URLS.get(request.user.role)
    if target is None:
        messages.error(request, "Your account role is not recognised.")
        return redirect("login")
    return redirect(target)


@role_required(["seeker"])
def dashboard_seeker_view(request):
    return render(request, "dashboards/seeker.html")


@role_required(["provider"])
def dashboard_provider_view(request):
    return render(request, "dashboards/provider.html")


@role_required(["artist"])
def dashboard_artist_view(request):
    return render(request, "dashboards/artist.html")


@role_required(["admin"])
def dashboard_admin_view(request):
    return render(request, "dashboards/admin.html")
