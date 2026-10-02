import asyncio

import pytest
from asgiref.sync import sync_to_async
from django.utils import timezone

from clinic.models import Appointment, Patient

HEADERS = [(b'origin', b'http://testserver'), (b'host', b'testserver')]


@pytest.mark.django_db(transaction=True)
def test_queue_snapshot_and_live_update(doctor, patient):
    from channels.testing import WebsocketCommunicator

    from config.asgi import application

    today = timezone.now().replace(hour=23, minute=0, second=0)
    Appointment.objects.create(doctor=doctor, patient=patient, scheduled_at=today)

    async def scenario():
        communicator = WebsocketCommunicator(application, '/ws/queue/', headers=HEADERS)
        connected, _ = await communicator.connect()
        assert connected

        snapshot = await communicator.receive_json_from()
        assert snapshot['type'] == 'queue.snapshot'
        assert len(snapshot['appointments']) == 1

        walk_in = await sync_to_async(Patient.objects.create)(
            first_name='Walk', last_name='In', email='walkin@x.com'
        )
        await sync_to_async(Appointment.objects.create)(
            doctor=doctor, patient=walk_in, scheduled_at=today.replace(minute=30)
        )

        update = await communicator.receive_json_from(timeout=5)
        assert update['type'] == 'queue.update'
        assert update['appointment']['patient'] == 'Walk In'

        await communicator.disconnect()

    asyncio.run(scenario())
