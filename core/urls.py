"""
core/urls.py — app-level routes, included from localhub_config/urls.py.
"""
from django.urls import path

from . import views

urlpatterns = [
    # Auth
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Post-login dispatcher
    path("dashboard/", views.role_dispatch_view, name="role_dispatch"),

    # Role dashboards
    path("dashboard/seeker/", views.dashboard_seeker_view, name="dashboard_seeker"),
    path("dashboard/provider/", views.dashboard_provider_view, name="dashboard_provider"),
    path("dashboard/artist/", views.dashboard_artist_view, name="dashboard_artist"),
    path("dashboard/admin/", views.dashboard_admin_view, name="dashboard_admin"),
]
