from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_appointment_confirmation(appointment_id):
    # Imported here so the task module stays importable before apps load.
    from .models import Appointment

    try:
        appointment = Appointment.objects.select_related('doctor', 'patient').get(
            pk=appointment_id
        )
    except Appointment.DoesNotExist:
        return f'Appointment {appointment_id} no longer exists.'

    patient = appointment.patient
    send_mail(
        subject='Your appointment is confirmed',
        message=(
            f'Hi {patient.first_name},\n\n'
            f'Your appointment with {appointment.doctor} is confirmed for '
            f'{appointment.scheduled_at:%A, %B %d at %H:%M} (UTC).\n\n'
            f'Reason: {appointment.reason or "—"}\n\n'
            'ClinicFlow'
        ),
        from_email=None,  # uses DEFAULT_FROM_EMAIL
        recipient_list=[patient.email],
    )
    return f'Confirmation sent to {patient.email}'
