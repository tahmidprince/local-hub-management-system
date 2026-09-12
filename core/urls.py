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

    # --- Account: profile management -----------------------------------
    path("profile/", views.profile_update_view, name="profile"),

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
    path("admin/item/<int:pk>/approve/", views.admin_approve_item_view, name="admin_approve_item"),
    path("admin/item/<int:pk>/reject/", views.admin_reject_item_view, name="admin_reject_item"),
    path("admin/withdrawal/<int:pk>/process/", views.admin_process_withdrawal_view, name="admin_process_withdrawal"),

    # --- Creative Shop: browse, cart, checkout ------------------------
    path("shop/", views.shop_catalog_view, name="shop_catalog"),
    path("shop/item/<int:pk>/", views.item_detail_view, name="item_detail"),
    path("cart/", views.cart_view, name="cart_view"),
    path("cart/add/<int:item_id>/", views.add_to_cart_view, name="add_to_cart"),
    path("cart/remove/<int:pk>/", views.cart_remove_view, name="cart_remove"),
    path("checkout/", views.checkout_view, name="checkout"),

    # --- Escrow payments & completion ---------------------------------
    path("payment/process/", views.process_payment_view, name="process_payment"),
    path("complete/task/<int:task_id>/", views.mark_task_completed_view, name="mark_task_completed"),
    path("complete/order/<int:order_id>/", views.mark_order_completed_view, name="mark_order_completed"),

    # --- Artist order fulfillment (shipping status + COD loop) ---------
    path("order/<int:order_id>/update-status/", views.update_order_status_view, name="update_order_status"),

    # --- Wallet withdrawals -------------------------------------------
    path("wallet/withdraw/", views.request_withdrawal_view, name="request_withdrawal"),
]
