"""
core/urls.py — app-level routes, included from localhub_config/urls.py.
"""
from django.urls import path

from . import views

urlpatterns = [
    # --- Auth -----------------------------------------------------
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # --- Post-login dispatcher -------------------------------------
    path("dashboard/", views.role_dispatch_view, name="role_dispatch"),

    # --- Seeker: post & manage tasks ---------------------------------
    path("dashboard/seeker/", views.dashboard_seeker_view, name="dashboard_seeker"),
    path("dashboard/seeker/tasks/<int:pk>/edit/", views.task_edit_view, name="task_edit"),
    path("dashboard/seeker/tasks/<int:pk>/delete/", views.task_delete_view, name="task_delete"),

    # --- Provider: browse tasks & bid ---------------------------------
    path("dashboard/provider/", views.dashboard_provider_view, name="dashboard_provider"),
    path("task/<int:pk>/", views.task_detail_view, name="task_detail"),
    path("proposal/<int:pk>/accept/", views.accept_proposal_view, name="accept_proposal"),

    # --- Artist: post & manage shop items -----------------------------
    path("dashboard/artist/", views.dashboard_artist_view, name="dashboard_artist"),
    path("dashboard/artist/items/<int:pk>/edit/", views.item_edit_view, name="item_edit"),
    path("dashboard/artist/items/<int:pk>/delete/", views.item_delete_view, name="item_delete"),
    path("dashboard/artist/items/<int:pk>/toggle/", views.item_toggle_active_view, name="item_toggle_active"),

    # --- Admin (placeholder, Part 1) ---------------------------------
    path("dashboard/admin/", views.dashboard_admin_view, name="dashboard_admin"),

    # --- Creative Shop: browse, cart, checkout ------------------------
    path("shop/", views.shop_catalog_view, name="shop_catalog"),
    path("shop/item/<int:pk>/", views.item_detail_view, name="item_detail"),
    path("cart/", views.cart_view, name="cart_view"),
    path("cart/add/<int:item_id>/", views.add_to_cart_view, name="add_to_cart"),
    path("cart/remove/<int:pk>/", views.cart_remove_view, name="cart_remove"),
    path("checkout/", views.checkout_view, name="checkout"),
]
