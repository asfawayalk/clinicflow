from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Profile
from clinic.models import Appointment, Doctor, Patient

DEMO_PASSWORD = 'demo-pass-123'


class Command(BaseCommand):
    help = 'Seed the database with demo users, doctors, patients, and appointments.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data...')

        admin = self.user('admin', is_staff=True, is_superuser=True)

        recep = self.user('receptionist', role=Profile.Role.RECEPTIONIST, first='Rita', last='Front')

        doctors = []
        for username, first, last, specialty in [
            ('dr.jane', 'Jane', 'Smith', Doctor.Specialty.CARDIOLOGY),
            ('dr.abel', 'Abel', 'Tesfaye', Doctor.Specialty.GENERAL),
            ('dr.sara', 'Sara', 'Bekele', Doctor.Specialty.PEDIATRICS),
        ]:
            user = self.user(username, role=Profile.Role.DOCTOR, first=first, last=last)
            doctor, _ = Doctor.objects.get_or_create(
                first_name=first, last_name=last, defaults={'specialty': specialty, 'user': user}
            )
            doctors.append(doctor)

        patients = []
        for username, first, last in [
            ('patient', 'Pat', 'Jones'),
            ('liya', 'Liya', 'Haile'),
            ('marcus', 'Marcus', 'Lee'),
            ('amira', 'Amira', 'Said'),
        ]:
            user = self.user(username, role=Profile.Role.PATIENT, first=first, last=last)
            patient, _ = Patient.objects.get_or_create(
                email=f'{username}@example.com',
                defaults={'first_name': first, 'last_name': last, 'user': user, 'phone': '+1 555 0100'},
            )
            patients.append(patient)

        # Today's queue: one checked in, two scheduled. Plus bookings tomorrow.
        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        slots = [
            (doctors[0], patients[0], now + timedelta(hours=1), Appointment.Status.CHECKED_IN, 'Follow-up'),
            (doctors[0], patients[1], now + timedelta(hours=2), Appointment.Status.SCHEDULED, 'Chest pain'),
            (doctors[1], patients[2], now + timedelta(hours=3), Appointment.Status.SCHEDULED, 'Annual checkup'),
            (doctors[1], patients[3], now + timedelta(days=1, hours=1), Appointment.Status.SCHEDULED, 'Headache'),
            (doctors[2], patients[1], now + timedelta(days=1, hours=2), Appointment.Status.SCHEDULED, 'Child vaccination'),
        ]
        created = 0
        for doctor, patient, when, status, reason in slots:
            _, was_created = Appointment.objects.get_or_create(
                doctor=doctor,
                scheduled_at=when,
                defaults={'patient': patient, 'status': status, 'reason': reason},
            )
            created += was_created

        self.stdout.write(self.style.SUCCESS(
            f'Done. {User.objects.count()} users, {Doctor.objects.count()} doctors, '
            f'{Patient.objects.count()} patients, {Appointment.objects.count()} appointments '
            f'({created} new).'
        ))
        self.stdout.write('')
        self.stdout.write(f'Demo logins (password for all: {DEMO_PASSWORD}):')
        self.stdout.write('  admin         — Django admin superuser')
        self.stdout.write('  receptionist  — full API access')
        self.stdout.write('  dr.jane       — sees her own appointments')
        self.stdout.write('  patient       — sees/books only their own appointments')

    def user(self, username, role=None, first='', last='', is_staff=False, is_superuser=False):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@example.com',
                'first_name': first,
                'last_name': last,
                'is_staff': is_staff,
                'is_superuser': is_superuser,
            },
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
        if role and user.profile.role != role:
            user.profile.role = role
            user.profile.save()
        return user
