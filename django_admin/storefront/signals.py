"""
storefront/signals.py
------------------------
Order.order_status is edited directly in the admin list view
(OrderAdmin.list_editable, see admin.py) — there's no separate "ship this
order" button, just changing the dropdown and saving. This signal is what
turns that save into an actual notification: it compares the status
before and after save, and if it just became SHIPPED or DELIVERED, calls
fastapi_backend's internal notify endpoint (POST /internal/notifications,
authenticated with a shared secret rather than a user JWT — see
core/config.py's INTERNAL_API_SECRET on the FastAPI side).

This is a synchronous HTTP call made from inside Django's request/response
cycle, so a slow or unreachable FastAPI backend would slow down or fail
the admin's save. For this project's scope that's an acceptable
trade-off — logged and swallowed on failure (see except below) so a
notification hiccup never blocks the admin from actually updating the
order — rather than introducing a task queue (Celery, etc.) just for this.
"""

import logging

import requests
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Order

logger = logging.getLogger("storefront.signals")

_STATUS_TO_EVENT = {
    "SHIPPED": "order_shipped",
    "DELIVERED": "order_delivered",
}


@receiver(pre_save, sender=Order)
def _stash_previous_status(sender, instance, **kwargs):
    """Order is unmanaged with no Django-tracked change history, so the
    only way to know "did order_status just change" is to look up what it
    was right before this save — stashed on the instance for post_save."""
    if not instance.pk:
        instance._previous_order_status = None
        return
    try:
        instance._previous_order_status = Order.objects.get(pk=instance.pk).order_status
    except Order.DoesNotExist:
        instance._previous_order_status = None


@receiver(post_save, sender=Order)
def _notify_on_status_change(sender, instance, created, **kwargs):
    if created:
        return  # orders are created by fastapi_backend's /checkout, never here

    previous_status = getattr(instance, "_previous_order_status", None)
    if previous_status == instance.order_status:
        return  # saved for some other reason (e.g. re-saving with no real change)

    event = _STATUS_TO_EVENT.get(instance.order_status)
    if not event:
        return  # only shipped/delivered are notification-worthy from here

    # NEW (Refund & Return milestone): stamp delivered_at the moment this
    # order is actually saved as DELIVERED — fastapi_backend's return
    # window check (routes/orders.py) is built on this timestamp.
    # QuerySet.update() bypasses save() entirely, so it does NOT re-fire
    # this same post_save signal — using instance.save() here instead
    # would cause infinite recursion.
    if instance.order_status == "DELIVERED" and not instance.delivered_at:
        Order.objects.filter(pk=instance.pk).update(delivered_at=timezone.now())

    try:
        response = requests.post(
            f"{settings.FASTAPI_INTERNAL_URL}/internal/notifications",
            json={"user_id": instance.user_id, "order_id": instance.id, "event": event},
            headers={"x-internal-secret": settings.INTERNAL_API_SECRET},
            timeout=5,
        )
        if response.status_code != 200:
            logger.warning(
                "fastapi_backend rejected the %s notification for order #%s: %s %s",
                event, instance.id, response.status_code, response.text,
            )
    except requests.RequestException:
        logger.exception(
            "Could not reach fastapi_backend to send the %s notification for order #%s — "
            "is uvicorn running on %s?",
            event, instance.id, settings.FASTAPI_INTERNAL_URL,
        )