"""
core/views.py

Part 1: register / login / logout / role dispatcher.
Part 3: Seeker dashboard (post + manage WorkEntry) and Artist dashboard
        (post + manage CreativeItem), each with basic edit/delete so the
        CRUD loop is actually complete, not just "create".
Part 4: Provider dashboard (browse + bid on tasks) and the seeker's
        bid-acceptance / task-assignment cascade.
Part 5: Creative Shop — public catalog/browsing, cart, and checkout.
"""
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .decorators import role_required
from .forms import (
    CreativeItemForm,
    TaskProposalForm,
    UserLoginForm,
    UserRegistrationForm,
    WorkEntryForm,
)
from .models import (
    CartItem,
    CreativeItem,
    Order,
    OrderItem,
    Payment,
    TaskProposal,
    User,
    WithdrawalRequest,
    WorkEntry,
)

ROLE_DASHBOARD_URLS = {
    "seeker": "dashboard_seeker",
    "provider": "dashboard_provider",
    "artist": "dashboard_artist",
    "admin": "dashboard_admin",
}


# =====================================================================
# PART 1 — AUTH
# =====================================================================


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
    target = ROLE_DASHBOARD_URLS.get(request.user.role)
    if target is None:
        messages.error(request, "Your account role is not recognised.")
        return redirect("login")
    return redirect(target)


# =====================================================================
# PART 3 — SEEKER DASHBOARD (post & manage tasks)
# =====================================================================


@role_required(["seeker"])
def dashboard_seeker_view(request):
    if request.method == "POST":
        form = WorkEntryForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.seeker = request.user
            task.save()
            messages.success(request, f'"{task.title}" was posted successfully.')
            return redirect("dashboard_seeker")
        messages.error(request, "Please fix the errors below and try again.")
    else:
        form = WorkEntryForm()

    posted_tasks = request.user.posted_tasks.all().order_by("-created_at")

    return render(request, "dashboards/seeker.html", {
        "form": form,
        "posted_tasks": posted_tasks,
    })


@role_required(["seeker"])
def task_edit_view(request, pk):
    task = get_object_or_404(WorkEntry, pk=pk, seeker=request.user)

    if task.status != WorkEntry.Status.POSTED:
        messages.error(request, "Only tasks that haven't been assigned yet can be edited.")
        return redirect("dashboard_seeker")

    if request.method == "POST":
        form = WorkEntryForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{task.title}" was updated.')
            return redirect("dashboard_seeker")
        messages.error(request, "Please fix the errors below and try again.")
    else:
        form = WorkEntryForm(instance=task)

    posted_tasks = request.user.posted_tasks.all().order_by("-created_at")

    return render(request, "dashboards/seeker.html", {
        "form": form,
        "posted_tasks": posted_tasks,
        "editing_task": task,
    })


@role_required(["seeker"])
def task_delete_view(request, pk):
    task = get_object_or_404(WorkEntry, pk=pk, seeker=request.user)

    if request.method == "POST":
        if task.status != WorkEntry.Status.POSTED:
            messages.error(request, "Only tasks that haven't been assigned yet can be deleted.")
        else:
            title = task.title
            task.delete()
            messages.success(request, f'"{title}" was deleted.')

    return redirect("dashboard_seeker")


# =====================================================================
# PART 3 — ARTIST DASHBOARD (post & manage shop items)
# =====================================================================


@role_required(["artist"])
def dashboard_artist_view(request):
    if request.method == "POST":
        form = CreativeItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.artist = request.user
            item.save()
            messages.success(
                request,
                f'"{item.item_name}" was added to your shop and is awaiting admin approval.'
            )
            return redirect("dashboard_artist")
        messages.error(request, "Please fix the errors below and try again.")
    else:
        form = CreativeItemForm()

    artworks = request.user.artworks.all().order_by("-created_at")

    incoming_orders = (
        OrderItem.objects.filter(item__artist=request.user)
        .select_related("order", "order__buyer", "item")
        .order_by("-order__created_at")
    )

    return render(request, "dashboards/artist.html", {
        "form": form,
        "artworks": artworks,
        "incoming_orders": incoming_orders,
    })


@role_required(["artist"])
def item_edit_view(request, pk):
    item = get_object_or_404(CreativeItem, pk=pk, artist=request.user)

    if request.method == "POST":
        form = CreativeItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{item.item_name}" was updated.')
            return redirect("dashboard_artist")
        messages.error(request, "Please fix the errors below and try again.")
    else:
        form = CreativeItemForm(instance=item)

    artworks = request.user.artworks.all().order_by("-created_at")

    return render(request, "dashboards/artist.html", {
        "form": form,
        "artworks": artworks,
        "editing_item": item,
    })


@role_required(["artist"])
def item_delete_view(request, pk):
    item = get_object_or_404(CreativeItem, pk=pk, artist=request.user)

    if request.method == "POST":
        name = item.item_name
        try:
            item.delete()
            messages.success(request, f'"{name}" was removed from your shop.')
        except ProtectedError:
            # item is referenced by one or more historical OrderItem rows
            # (on_delete=PROTECT) — unlist it instead of hard-deleting.
            item.is_active = False
            item.save(update_fields=["is_active"])
            messages.warning(
                request,
                f'"{name}" has past orders attached, so it can\'t be deleted — '
                "it's been unlisted instead."
            )

    return redirect("dashboard_artist")


@role_required(["artist"])
def item_toggle_active_view(request, pk):
    """Quick in/out-of-listing toggle, separate from a full edit."""
    item = get_object_or_404(CreativeItem, pk=pk, artist=request.user)

    if request.method == "POST":
        item.is_active = not item.is_active
        item.save(update_fields=["is_active"])
        state = "listed" if item.is_active else "unlisted"
        messages.success(request, f'"{item.item_name}" is now {state}.')

    return redirect("dashboard_artist")


# =====================================================================
# PART 4 — PROVIDER DASHBOARD (browse & bid on tasks)
# =====================================================================


@role_required(["provider"])
def dashboard_provider_view(request):
    available_tasks = WorkEntry.objects.filter(
        status=WorkEntry.Status.POSTED
    ).order_by("-created_at")

    my_bids = request.user.proposals.all().order_by("-created_at")

    return render(request, "dashboards/provider.html", {
        "available_tasks": available_tasks,
        "my_bids": my_bids,
    })


@login_required
def task_detail_view(request, pk):
    """
    Dual-purpose task page:
    - A provider sees the task and can submit/view their own bid.
    - The seeker who posted the task sees every submitted proposal,
      with an "Accept" action on each pending one.
    Anyone else (wrong role, or a provider/seeker with no stake in
    this task) gets redirected back to their own dashboard.
    """
    task = get_object_or_404(WorkEntry, pk=pk)
    is_owner = task.seeker_id == request.user.id

    if not is_owner and request.user.role != User.Role.PROVIDER:
        messages.error(request, "You do not have permission to view that page.")
        return redirect("role_dispatch")

    context = {"task": task, "is_owner": is_owner}

    if is_owner:
        context["proposals"] = task.proposals.select_related("provider").order_by(
            "-created_at"
        )
        return render(request, "tasks/task_detail.html", context)

    # --- Provider branch -------------------------------------------
    existing_proposal = TaskProposal.objects.filter(
        task=task, provider=request.user
    ).first()

    can_bid = task.status == WorkEntry.Status.POSTED and existing_proposal is None
    form = None

    if request.method == "POST":
        if not can_bid:
            messages.error(request, "This task is no longer open for bids.")
            return redirect("task_detail", pk=task.pk)

        form = TaskProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.task = task
            proposal.provider = request.user
            try:
                proposal.save()
            except IntegrityError:
                # Race condition: a duplicate bid slipped in between the
                # existence check above and this save.
                messages.error(request, "You've already placed a bid on this task.")
            else:
                messages.success(request, "Your bid was submitted successfully.")
                return redirect("dashboard_provider")
        else:
            messages.error(request, "Please fix the errors below and try again.")
    elif can_bid:
        form = TaskProposalForm()

    context.update({
        "form": form,
        "can_bid": can_bid,
        "existing_proposal": existing_proposal,
    })
    return render(request, "tasks/task_detail.html", context)


@role_required(["seeker"])
def accept_proposal_view(request, pk):
    """
    POST-only. The seeker accepts one proposal on their own task:
    - that proposal -> accepted
    - every other pending proposal on the same task -> rejected
    - the task itself -> assigned, with `provider` set to the winner

    Wrapped in a transaction so a mid-way failure can't leave the task
    assigned to a provider whose proposal didn't actually get flipped
    to accepted (or vice versa).
    """
    if request.method != "POST":
        return redirect("role_dispatch")

    proposal = get_object_or_404(
        TaskProposal.objects.select_related("task"), pk=pk
    )
    task = proposal.task

    if task.seeker_id != request.user.id:
        messages.error(request, "You do not have permission to do that.")
        return redirect("role_dispatch")

    if task.status != WorkEntry.Status.POSTED or proposal.status != TaskProposal.Status.PENDING:
        messages.error(request, "This proposal can no longer be accepted.")
        return redirect("task_detail", pk=task.pk)

    with transaction.atomic():
        proposal.status = TaskProposal.Status.ACCEPTED
        proposal.save(update_fields=["status"])

        task.proposals.filter(
            status=TaskProposal.Status.PENDING
        ).exclude(pk=proposal.pk).update(status=TaskProposal.Status.REJECTED)

        task.status = WorkEntry.Status.ASSIGNED
        task.provider = proposal.provider
        task.save(update_fields=["status", "provider", "updated_at"])

    messages.success(
        request, f"{proposal.provider.full_name}'s bid was accepted for \"{task.title}\"."
        " Fund the task now to move it into progress."
    )
    return redirect(f"{reverse('process_payment')}?task_id={task.pk}")


# =====================================================================
# PART 5 — CREATIVE SHOP: BROWSE, CART, CHECKOUT
# =====================================================================


def shop_catalog_view(request):
    """
    Public product grid. No login required — browsing shouldn't be
    gated behind an account, only buying. Only shows items that are
    both switched on by the artist (is_active) AND cleared by an admin
    (is_approved) — an artist listing something doesn't make it public
    on its own anymore.
    """
    items = (
        CreativeItem.objects.filter(
            is_active=True, is_approved=True, stock_quantity__gt=0
        )
        .select_related("artist")
        .order_by("-created_at")
    )
    return render(request, "shop/catalog.html", {"items": items})


def item_detail_view(request, pk):
    """
    Full item showcase. GET is public; the "Add to Cart" POST requires
    login (bounced to the login page with ?next= back to this item).
    """
    item = get_object_or_404(CreativeItem, pk=pk, is_active=True)

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.info(request, "Please log in to add items to your cart.")
            return redirect(f"{reverse('login')}?next={request.path}")

        if item.stock_quantity < 1:
            messages.error(request, "This item is currently out of stock.")
            return redirect("item_detail", pk=item.pk)

        try:
            quantity = int(request.POST.get("quantity", 1))
        except (TypeError, ValueError):
            quantity = 1
        quantity = max(1, min(quantity, item.stock_quantity))

        cart_item, created = CartItem.objects.get_or_create(
            user=request.user, item=item, defaults={"quantity": quantity}
        )
        if not created:
            new_quantity = min(cart_item.quantity + quantity, item.stock_quantity)
            if new_quantity == cart_item.quantity:
                messages.warning(
                    request,
                    f"You already have the maximum available stock of "
                    f'"{item.item_name}" in your cart.'
                )
            else:
                cart_item.quantity = new_quantity
                cart_item.save(update_fields=["quantity"])
                messages.success(request, f'"{item.item_name}" quantity updated in your cart.')
        else:
            messages.success(request, f'"{item.item_name}" was added to your cart.')

        return redirect("cart_view")

    return render(request, "shop/item_detail.html", {"item": item})


@login_required
def add_to_cart_view(request, item_id):
    """
    POST-only "quick add" from the catalog grid — always adds a single
    unit, or increments by one if the item is already in the cart.
    """
    if request.method != "POST":
        return redirect("shop_catalog")

    item = get_object_or_404(CreativeItem, pk=item_id, is_active=True)

    if item.stock_quantity < 1:
        messages.error(request, "This item is currently out of stock.")
        return redirect("shop_catalog")

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user, item=item, defaults={"quantity": 1}
    )
    if not created:
        if cart_item.quantity >= item.stock_quantity:
            messages.error(
                request,
                f'Only {item.stock_quantity} of "{item.item_name}" in stock — '
                "you already have that many in your cart."
            )
        else:
            cart_item.quantity += 1
            cart_item.save(update_fields=["quantity"])
            messages.success(request, f'"{item.item_name}" quantity updated in your cart.')
    else:
        messages.success(request, f'"{item.item_name}" was added to your cart.')

    next_url = request.POST.get("next")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)
    return redirect("cart_view")


@login_required
def cart_view(request):
    cart_items = (
        request.user.cart_items.select_related("item", "item__artist").all()
    )
    total_amount = sum((ci.line_total for ci in cart_items), Decimal("0.00"))

    return render(request, "shop/cart.html", {
        "cart_items": cart_items,
        "total_amount": total_amount,
    })


@login_required
def cart_remove_view(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, user=request.user)

    if request.method == "POST":
        name = cart_item.item.item_name
        cart_item.delete()
        messages.success(request, f'"{name}" was removed from your cart.')

    return redirect("cart_view")


@login_required
def checkout_view(request):
    cart_items = list(
        request.user.cart_items.select_related("item", "item__artist").all()
    )

    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect("cart_view")

    total_amount = sum((ci.line_total for ci in cart_items), Decimal("0.00"))

    if request.method == "POST":
        shipping_address = request.POST.get("shipping_address", "").strip()
        if not shipping_address:
            messages.error(request, "Please provide a shipping address.")
            return render(request, "shop/checkout.html", {
                "cart_items": cart_items,
                "total_amount": total_amount,
                "shipping_address": shipping_address,
            })

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    buyer=request.user,
                    total_amount=Decimal("0.00"),
                    shipping_address=shipping_address,
                )

                running_total = Decimal("0.00")
                # Re-fetch each item with a row lock so two simultaneous
                # checkouts can't both oversell the last unit of stock.
                for cart_item in cart_items:
                    item = CreativeItem.objects.select_for_update().get(
                        pk=cart_item.item_id
                    )
                    if item.stock_quantity < cart_item.quantity:
                        raise ValueError(
                            f'Not enough stock for "{item.item_name}" — '
                            f"only {item.stock_quantity} left."
                        )

                    OrderItem.objects.create(
                        order=order,
                        item=item,
                        quantity=cart_item.quantity,
                        unit_price=item.price,
                        subtotal=item.price * cart_item.quantity,
                    )
                    item.stock_quantity -= cart_item.quantity
                    item.save(update_fields=["stock_quantity"])
                    running_total += item.price * cart_item.quantity

                order.total_amount = running_total
                order.save(update_fields=["total_amount"])

                request.user.cart_items.all().delete()
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("cart_view")

        messages.success(
            request,
            f"Order #{order.pk} created! Total: \u09f3{order.total_amount}. Complete payment to confirm it."
        )
        return redirect(f"{reverse('process_payment')}?order_id={order.pk}")

    return render(request, "shop/checkout.html", {
        "cart_items": cart_items,
        "total_amount": total_amount,
        "shipping_address": "",
    })


# =====================================================================
# PART 6 — ESCROW PAYMENTS & COMPLETION
# =====================================================================


def _release_payment_to_recipient(payment):
    """
    Flip an escrowed Payment to `released` and credit the amount onto
    the recipient's `User.wallet_balance`.

    NOTE: the spec for this step asked for `Profile.wallet_balance`,
    but the actual schema (Step 1) put `wallet_balance` on `User`
    itself — `Profile` has no such field. This credits `User.wallet_balance`
    since that's the field that really exists; see the accompanying
    note for how to migrate this onto Profile instead, if that's what
    you actually want.

    Locks the recipient's row for the duration of the update so two
    payouts landing on the same wallet at once can't race and drop one.
    """
    if payment.recipient_id is None:
        return False

    recipient = User.objects.select_for_update().get(pk=payment.recipient_id)
    recipient.wallet_balance = recipient.wallet_balance + payment.amount
    recipient.save(update_fields=["wallet_balance"])

    payment.status = Payment.Status.RELEASED
    payment.save(update_fields=["status"])
    return True


@login_required
def process_payment_view(request):
    """
    Simulated payment gateway. Takes exactly one of ?task_id= or
    ?order_id= and funds escrow for it. On success:
      - task  -> WorkEntry.status becomes 'in_progress'
      - order -> Order.status becomes 'paid'
    """
    task_id = request.GET.get("task_id")
    order_id = request.GET.get("order_id")

    if bool(task_id) == bool(order_id):  # neither, or both — invalid either way
        messages.error(request, "A payment must reference exactly one task or order.")
        return redirect("role_dispatch")

    task = None
    order = None

    if task_id:
        task = get_object_or_404(WorkEntry, pk=task_id)

        if request.user.id != task.seeker_id:
            messages.error(request, "You do not have permission to fund this task.")
            return redirect("role_dispatch")

        if task.status != WorkEntry.Status.ASSIGNED:
            messages.error(request, "This task isn't awaiting payment.")
            return redirect("task_detail", pk=task.pk)

        if Payment.objects.filter(
            task=task,
            status__in=[Payment.Status.HELD_IN_ESCROW, Payment.Status.RELEASED],
        ).exists():
            messages.info(request, "This task has already been funded.")
            return redirect("task_detail", pk=task.pk)

        amount = task.budget
        recipient = task.provider

    else:
        order = get_object_or_404(Order, pk=order_id)

        if request.user.id != order.buyer_id:
            messages.error(request, "You do not have permission to pay for this order.")
            return redirect("role_dispatch")

        if order.status != Order.Status.PENDING:
            messages.error(request, "This order isn't awaiting payment.")
            return redirect("role_dispatch")

        if Payment.objects.filter(
            order=order,
            status__in=[Payment.Status.HELD_IN_ESCROW, Payment.Status.RELEASED],
        ).exists():
            messages.info(request, "This order has already been paid.")
            return redirect("role_dispatch")

        amount = order.total_amount

        # An Order can (in principle) bundle items from several artists;
        # Payment.recipient is a single FK, so we can only auto-assign a
        # payout target when every line item shares one artist. Mixed-
        # artist orders fall back to recipient=None (platform-held) —
        # splitting a single Order into a Payment-per-artist is a
        # reasonable next step but out of scope here.
        artist_ids = set(
            order.items.select_related("item__artist").values_list(
                "item__artist_id", flat=True
            )
        )
        recipient = None
        if len(artist_ids) == 1:
            recipient = order.items.select_related("item__artist").first().item.artist

    if request.method == "POST":
        payment_method = request.POST.get("payment_method", "")
        transaction_id = request.POST.get("transaction_id", "").strip()

        if payment_method not in Payment.Method.values:
            messages.error(request, "Please choose a valid payment method.")
        elif not transaction_id:
            messages.error(request, "Please enter a transaction ID.")
        else:
            try:
                with transaction.atomic():
                    Payment.objects.create(
                        payer=request.user,
                        recipient=recipient,
                        task=task,
                        order=order,
                        amount=amount,
                        payment_method=payment_method,
                        transaction_id=transaction_id,
                        status=Payment.Status.HELD_IN_ESCROW,
                    )

                    if task:
                        task.status = WorkEntry.Status.IN_PROGRESS
                        task.save(update_fields=["status", "updated_at"])
                    else:
                        order.status = Order.Status.PAID
                        order.save(update_fields=["status"])
            except IntegrityError:
                messages.error(request, "That transaction ID has already been used.")
            else:
                messages.success(request, "Payment received — funds are held in escrow.")
                if task:
                    return redirect("task_detail", pk=task.pk)
                return redirect("role_dispatch")

    return render(request, "finance/payment_gateway.html", {
        "task": task,
        "order": order,
        "amount": amount,
        "payment_methods": Payment.Method.choices,
    })


@role_required(["seeker"])
def mark_task_completed_view(request, task_id):
    """
    The seeker confirms a funded task is done: task -> completed, and
    the escrowed Payment for it -> released, crediting the provider's
    wallet.
    """
    task = get_object_or_404(WorkEntry, pk=task_id)

    if request.user.id != task.seeker_id:
        messages.error(request, "You do not have permission to do that.")
        return redirect("role_dispatch")

    if request.method != "POST":
        return redirect("task_detail", pk=task.pk)

    if task.status != WorkEntry.Status.IN_PROGRESS:
        messages.error(request, "This task isn't in progress, so it can't be marked completed.")
        return redirect("task_detail", pk=task.pk)

    with transaction.atomic():
        task.status = WorkEntry.Status.COMPLETED
        task.save(update_fields=["status", "updated_at"])

        payment = Payment.objects.select_for_update().filter(
            task=task, status=Payment.Status.HELD_IN_ESCROW
        ).first()

        if payment:
            _release_payment_to_recipient(payment)
        else:
            messages.warning(
                request,
                "Task marked completed, but no escrowed payment was found to release."
            )

    messages.success(
        request,
        f'"{task.title}" was marked completed and payment released to the provider.'
    )
    return redirect("task_detail", pk=task.pk)


@role_required(["artist"])
def mark_order_completed_view(request, order_id):
    """
    The fulfilling artist confirms an order is delivered: order ->
    delivered (Order has no 'completed' status — 'delivered' is its
    terminal, fulfilled state), and the escrowed Payment for it ->
    released, crediting the artist's wallet.

    Only works for orders with a single, unambiguous recipient artist
    (see the mixed-artist note in process_payment_view).
    """
    order = get_object_or_404(Order, pk=order_id)

    payment = Payment.objects.filter(
        order=order, status=Payment.Status.HELD_IN_ESCROW
    ).first()

    if payment is None or payment.recipient_id != request.user.id:
        messages.error(request, "You do not have permission to do that.")
        return redirect("role_dispatch")

    if request.method != "POST":
        return redirect("role_dispatch")

    if order.status != Order.Status.PAID:
        messages.error(request, "This order isn't awaiting fulfillment.")
        return redirect("role_dispatch")

    with transaction.atomic():
        order.status = Order.Status.DELIVERED
        order.save(update_fields=["status"])

        locked_payment = Payment.objects.select_for_update().get(pk=payment.pk)
        _release_payment_to_recipient(locked_payment)

    messages.success(request, f"Order #{order.pk} was marked delivered and payment released.")
    return redirect("role_dispatch")


# =====================================================================
# PART 7 — WALLET WITHDRAWALS & ADMIN MODERATION
# =====================================================================


@role_required(["provider", "artist"])
def request_withdrawal_view(request):
    """
    POST-only. Reserves funds immediately (deducted from the wallet the
    moment the request is made, not when an admin later approves it) so
    the same balance can't be withdrawn twice while a request is
    pending. If an admin later rejects it, the funds are refunded (see
    admin_process_withdrawal_view).
    """
    if request.method != "POST":
        return redirect("role_dispatch")

    method = request.POST.get("method", "")
    account_details = request.POST.get("account_details", "").strip()
    amount_raw = request.POST.get("amount", "").strip()

    try:
        amount = Decimal(amount_raw)
    except (InvalidOperation, ValueError, TypeError):
        messages.error(request, "Please enter a valid withdrawal amount.")
        return redirect("role_dispatch")

    if amount <= 0:
        messages.error(request, "Withdrawal amount must be greater than zero.")
        return redirect("role_dispatch")

    if method not in WithdrawalRequest.Method.values:
        messages.error(request, "Please choose a valid withdrawal method.")
        return redirect("role_dispatch")

    if not account_details:
        messages.error(request, "Please provide your account/phone number.")
        return redirect("role_dispatch")

    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=request.user.pk)

        if amount > user.wallet_balance:
            messages.error(request, "You can't withdraw more than your wallet balance.")
            return redirect("role_dispatch")

        user.wallet_balance = user.wallet_balance - amount
        user.save(update_fields=["wallet_balance"])

        WithdrawalRequest.objects.create(
            user=user,
            amount=amount,
            method=method,
            account_details=account_details,
            status=WithdrawalRequest.Status.PENDING,
        )

    messages.success(
        request,
        f"Withdrawal request for \u09f3{amount} submitted — funds have been "
        "reserved from your wallet and will be sent once processed."
    )
    return redirect("role_dispatch")


@role_required(["admin"])
def dashboard_admin_view(request):
    pending_items = (
        CreativeItem.objects.filter(is_approved=False)
        .select_related("artist")
        .order_by("-created_at")
    )
    pending_withdrawals = (
        WithdrawalRequest.objects.filter(status=WithdrawalRequest.Status.PENDING)
        .select_related("user")
        .order_by("created_at")
    )

    return render(request, "dashboards/admin.html", {
        "pending_items": pending_items,
        "pending_withdrawals": pending_withdrawals,
    })


@role_required(["admin"])
def admin_approve_item_view(request, pk):
    item = get_object_or_404(CreativeItem, pk=pk)

    if request.method == "POST":
        item.is_approved = True
        item.save(update_fields=["is_approved"])
        messages.success(
            request, f'"{item.item_name}" was approved and is now live in the shop.'
        )

    return redirect("dashboard_admin")


@role_required(["admin"])
def admin_process_withdrawal_view(request, pk):
    """
    POST-only. `action=complete` marks the (already-deducted) request
    as paid out. `action=reject` refunds the reserved amount back onto
    the user's wallet — since request_withdrawal_view deducts on
    submission, a rejection with no refund would just delete the
    user's money.
    """
    withdrawal = get_object_or_404(WithdrawalRequest, pk=pk)

    if request.method != "POST":
        return redirect("dashboard_admin")

    if withdrawal.status != WithdrawalRequest.Status.PENDING:
        messages.error(request, "This withdrawal request has already been processed.")
        return redirect("dashboard_admin")

    action = request.POST.get("action")

    if action == "complete":
        withdrawal.status = WithdrawalRequest.Status.COMPLETED
        withdrawal.save(update_fields=["status"])
        messages.success(
            request,
            f"Withdrawal of \u09f3{withdrawal.amount} for {withdrawal.user.full_name} marked as paid."
        )
    elif action == "reject":
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=withdrawal.user_id)
            user.wallet_balance = user.wallet_balance + withdrawal.amount
            user.save(update_fields=["wallet_balance"])

            withdrawal.status = WithdrawalRequest.Status.REJECTED
            withdrawal.save(update_fields=["status"])

        messages.info(
            request,
            f"Withdrawal request for {withdrawal.user.full_name} was rejected and "
            f"\u09f3{withdrawal.amount} refunded to their wallet."
        )
    else:
        messages.error(request, "Unknown action.")

    return redirect("dashboard_admin")
