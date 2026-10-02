from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Appointment
from .tasks import send_appointment_confirmation


@receiver(post_save, sender=Appointment)
def queue_confirmation_email(sender, instance, created, **kwargs):
    if created:
        # Queue only after the transaction commits, so the worker can see the row.
        transaction.on_commit(
            lambda: send_appointment_confirmation.delay(instance.pk)
        )
