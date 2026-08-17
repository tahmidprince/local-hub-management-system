"""
core/signals.py

Auto-create (and keep in sync) a Profile whenever a User is created.
Registered in CoreConfig.ready() to avoid circular imports / app-registry
issues at import time.
"""
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_sync_user_profile(sender, instance, created, **kwargs):
    """
    On first save: create the related Profile.
    On subsequent saves: make sure a Profile exists (defensive, in case
    a User was created outside of Django, e.g. via a data migration)
    and persist it so any signal-driven Profile logic stays current.
    """
    if created:
        Profile.objects.create(user=instance)
        return

    Profile.objects.get_or_create(user=instance)
