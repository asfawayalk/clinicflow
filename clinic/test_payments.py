import hashlib
import hmac
import json
import time
from unittest.mock import MagicMock, patch

import pytest
from rest_framework.test import APIClient

from clinic.models import Appointment, Payment

WEBHOOK_SECRET = 'whsec_testsecret'


@pytest.fixture
def appointment(doctor, patient):
    return Appointment.objects.create(
        doctor=doctor, patient=patient, scheduled_at='2030-01-15T09:00:00Z'
    )


@pytest.fixture
def stripe_settings(settings):
    settings.STRIPE_SECRET_KEY = 'sk_test_fake'
    settings.STRIPE_WEBHOOK_SECRET = WEBHOOK_SECRET
    return settings


def signed_webhook(payload: bytes):
    timestamp = str(int(time.time()))
    signature = hmac.new(
        WEBHOOK_SECRET.encode(), f'{timestamp}.'.encode() + payload, hashlib.sha256
    ).hexdigest()
    return APIClient().post(
        '/api/stripe/webhook/',
        data=payload,
        content_type='application/json',
        headers={'Stripe-Signature': f't={timestamp},v1={signature}'},
    )


@pytest.mark.django_db
class TestCheckout:
    def test_pay_returns_checkout_url(self, stripe_settings, patient_client, appointment):
        session = MagicMock(id='cs_test_1', url='https://checkout.stripe.com/pay/cs_test_1')
        with patch('stripe.checkout.Session.create', return_value=session) as create:
            response = patient_client.post(f'/api/appointments/{appointment.id}/pay/')
        assert response.status_code == 200
        assert response.json()['checkout_url'] == session.url
        amount = create.call_args.kwargs['line_items'][0]['price_data']['unit_amount']
        assert amount == stripe_settings.BOOKING_FEE_CENTS
        payment = Payment.objects.get(appointment=appointment)
        assert payment.status == Payment.Status.PENDING
        assert payment.stripe_session_id == 'cs_test_1'

    def test_pay_unconfigured_returns_503(self, patient_client, appointment, settings):
        settings.STRIPE_SECRET_KEY = ''
        response = patient_client.post(f'/api/appointments/{appointment.id}/pay/')
        assert response.status_code == 503

    def test_pay_twice_blocked_once_paid(self, stripe_settings, patient_client, appointment):
        Payment.objects.create(
            appointment=appointment, amount_cents=2000, status=Payment.Status.PAID
        )
        response = patient_client.post(f'/api/appointments/{appointment.id}/pay/')
        assert response.status_code == 400


@pytest.mark.django_db
class TestWebhook:
    def test_completed_session_marks_payment_paid(self, stripe_settings, appointment):
        Payment.objects.create(
            appointment=appointment, amount_cents=2000, stripe_session_id='cs_test_1'
        )
        payload = json.dumps(
            {'type': 'checkout.session.completed', 'data': {'object': {'id': 'cs_test_1'}}}
        ).encode()
        response = signed_webhook(payload)
        assert response.status_code == 200
        assert Payment.objects.get(appointment=appointment).status == Payment.Status.PAID

    def test_invalid_signature_rejected(self, stripe_settings, appointment):
        response = APIClient().post(
            '/api/stripe/webhook/',
            data=b'{}',
            content_type='application/json',
            headers={'Stripe-Signature': 't=1,v1=forged'},
        )
        assert response.status_code == 400

    def test_unknown_session_acknowledged(self, stripe_settings):
        payload = json.dumps(
            {'type': 'checkout.session.completed', 'data': {'object': {'id': 'cs_unknown'}}}
        ).encode()
        response = signed_webhook(payload)
        assert response.status_code == 200
        assert response.json()['matched'] is False
