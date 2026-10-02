from datetime import timedelta

import pytest
from django.utils import timezone

from clinic.models import Appointment, Patient
from clinic.tasks import send_appointment_reminders


@pytest.mark.django_db
class TestReminders:
    def test_reminds_only_tomorrows_scheduled_appointments(self, doctor, patient, mailoutbox):
        tomorrow = timezone.now().replace(hour=9, minute=0, second=0) + timedelta(days=1)
        next_week_patient = Patient.objects.create(
            first_name='Next', last_name='Week', email='nw@x.com'
        )
        cancelled_patient = Patient.objects.create(
            first_name='Can', last_name='Celled', email='cc@x.com'
        )
        Appointment.objects.create(doctor=doctor, patient=patient, scheduled_at=tomorrow)
        Appointment.objects.create(
            doctor=doctor, patient=next_week_patient, scheduled_at=tomorrow + timedelta(days=6)
        )
        Appointment.objects.create(
            doctor=doctor,
            patient=cancelled_patient,
            scheduled_at=tomorrow + timedelta(hours=1),
            status=Appointment.Status.CANCELLED,
        )
        mailoutbox.clear()  # drop booking-confirmation emails

        result = send_appointment_reminders()

        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == [patient.email]
        assert 'tomorrow' in mailoutbox[0].subject
        assert result.startswith('Sent 1 reminder')
