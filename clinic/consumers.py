from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

QUEUE_GROUP = 'waiting_room_queue'


def appointment_payload(appointment):
    return {
        'id': appointment.pk,
        'patient': str(appointment.patient),
        'doctor': str(appointment.doctor),
        'scheduled_at': appointment.scheduled_at.isoformat(),
        'status': appointment.status,
    }


class QueueConsumer(AsyncJsonWebsocketConsumer):
    """Waiting-room display: today's queue on connect, then live updates."""

    async def connect(self):
        await self.channel_layer.group_add(QUEUE_GROUP, self.channel_name)
        await self.accept()
        await self.send_json({'type': 'queue.snapshot', 'appointments': await self.todays_queue()})

    async def disconnect(self, code):
        await self.channel_layer.group_discard(QUEUE_GROUP, self.channel_name)

    async def queue_update(self, event):
        """Handler for `queue.update` messages broadcast to the group."""
        await self.send_json({'type': 'queue.update', 'appointment': event['appointment']})

    @database_sync_to_async
    def todays_queue(self):
        from .models import Appointment

        today = timezone.localdate()
        return [
            appointment_payload(a)
            for a in Appointment.objects.filter(scheduled_at__date=today)
            .exclude(status=Appointment.Status.CANCELLED)
            .select_related('doctor', 'patient')
        ]
