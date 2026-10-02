import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from accounts.models import Profile
from clinic.models import Doctor, Patient


@pytest.fixture
def receptionist(db):
    user = User.objects.create_user('recep', password='x')
    user.profile.role = Profile.Role.RECEPTIONIST
    user.profile.save()
    return user


@pytest.fixture
def doctor_user(db):
    user = User.objects.create_user('drjane', password='x')
    user.profile.role = Profile.Role.DOCTOR
    user.profile.save()
    return user


@pytest.fixture
def doctor(doctor_user):
    return Doctor.objects.create(user=doctor_user, first_name='Jane', last_name='Smith')


@pytest.fixture
def patient_user(db):
    user = User.objects.create_user('pat', password='x', first_name='Pat')
    return user


@pytest.fixture
def patient(patient_user):
    return Patient.objects.create(
        user=patient_user, first_name='Pat', last_name='Jones', email='pat@example.com'
    )


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def receptionist_client(receptionist):
    return client_for(receptionist)


@pytest.fixture
def doctor_client(doctor_user):
    return client_for(doctor_user)


@pytest.fixture
def patient_client(patient_user):
    return client_for(patient_user)
