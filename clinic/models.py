from django.conf import settings
from django.db import models


class Doctor(models.Model):
    class Specialty(models.TextChoices):
        GENERAL = 'general', 'General Practice'
        PEDIATRICS = 'pediatrics', 'Pediatrics'
        CARDIOLOGY = 'cardiology', 'Cardiology'
        DERMATOLOGY = 'dermatology', 'Dermatology'
        ORTHOPEDICS = 'orthopedics', 'Orthopedics'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='doctor_record',
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    specialty = models.CharField(
        max_length=20, choices=Specialty.choices, default=Specialty.GENERAL
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'Dr. {self.first_name} {self.last_name} ({self.get_specialty_display()})'


class Patient(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patient_record',
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Appointment(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        CHECKED_IN = 'checked_in', 'Checked in'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name='appointments')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    scheduled_at = models.DateTimeField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED
    )
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_at']
        constraints = [
            # A doctor cannot have two appointments at the same time slot.
            models.UniqueConstraint(
                fields=['doctor', 'scheduled_at'],
                condition=~models.Q(status='cancelled'),
                name='unique_doctor_timeslot',
            ),
        ]

    def __str__(self):
        return f'{self.patient} with {self.doctor} at {self.scheduled_at:%Y-%m-%d %H:%M}'


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'

    appointment = models.OneToOneField(
        Appointment, on_delete=models.CASCADE, related_name='payment'
    )
    amount_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default='usd')
    stripe_session_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.amount_cents / 100:.2f} {self.currency.upper()} for appointment {self.appointment_id} ({self.status})'
