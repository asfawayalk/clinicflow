import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from accounts.models import Profile
from clinic.models import Patient

REGISTER = {
    'username': 'newuser',
    'email': 'new@example.com',
    'password': 'Str0ng-pass-123',
    'first_name': 'New',
}


@pytest.mark.django_db
class TestRegistration:
    def test_register_creates_patient_profile_and_record(self):
        response = APIClient().post('/api/auth/register/', REGISTER, format='json')
        assert response.status_code == 201
        user = User.objects.get(username='newuser')
        assert user.profile.role == Profile.Role.PATIENT
        assert Patient.objects.filter(user=user, email='new@example.com').exists()

    def test_register_rejects_weak_password(self):
        response = APIClient().post(
            '/api/auth/register/', {**REGISTER, 'password': '123'}, format='json'
        )
        assert response.status_code == 400
        assert 'password' in response.json()

    def test_register_rejects_duplicate_email(self):
        APIClient().post('/api/auth/register/', REGISTER, format='json')
        response = APIClient().post(
            '/api/auth/register/', {**REGISTER, 'username': 'other'}, format='json'
        )
        assert response.status_code == 400
        assert 'email' in response.json()

    def test_password_is_not_echoed_back(self):
        response = APIClient().post('/api/auth/register/', REGISTER, format='json')
        assert 'password' not in response.json()


@pytest.mark.django_db
class TestJwtFlow:
    def test_token_refresh_and_me(self):
        client = APIClient()
        client.post('/api/auth/register/', REGISTER, format='json')

        response = client.post(
            '/api/auth/token/',
            {'username': 'newuser', 'password': 'Str0ng-pass-123'},
            format='json',
        )
        assert response.status_code == 200
        tokens = response.json()

        refreshed = client.post(
            '/api/auth/token/refresh/', {'refresh': tokens['refresh']}, format='json'
        )
        assert refreshed.status_code == 200

        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        me = client.get('/api/auth/me/')
        assert me.status_code == 200
        assert me.json()['username'] == 'newuser'
        assert me.json()['role'] == Profile.Role.PATIENT

    def test_wrong_password_rejected(self):
        APIClient().post('/api/auth/register/', REGISTER, format='json')
        response = APIClient().post(
            '/api/auth/token/', {'username': 'newuser', 'password': 'wrong'}, format='json'
        )
        assert response.status_code == 401

    def test_endpoints_require_authentication(self):
        assert APIClient().get('/api/doctors/').status_code == 401
        assert APIClient().get('/api/appointments/').status_code == 401
