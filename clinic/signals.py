from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .consumers import QUEUE_GROUP, appointment_payload
from .models import Appointment
from .tasks import send_appointment_confirmation


@receiver(post_save, sender=Appointment)
def queue_confirmation_email(sender, instance, created, **kwargs):
    if created:
        # Queue only after the transaction commits, so the worker can see the row.
        transaction.on_commit(
            lambda: send_appointment_confirmation.delay(instance.pk)
        )


@receiver(post_save, sender=Appointment)
def broadcast_queue_update(sender, instance, **kwargs):
    """Push every appointment create/status change to the live waiting-room queue."""

    def _broadcast():
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            QUEUE_GROUP,
            {'type': 'queue.update', 'appointment': appointment_payload(instance)},
        )

    transaction.on_commit(_broadcast)
