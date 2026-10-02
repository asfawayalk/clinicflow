import stripe
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment


def create_checkout_session(appointment):
    """Create a Stripe Checkout session for the appointment's booking fee."""
    stripe.api_key = settings.STRIPE_SECRET_KEY
    payment, _ = Payment.objects.get_or_create(
        appointment=appointment,
        defaults={'amount_cents': settings.BOOKING_FEE_CENTS},
    )
    session = stripe.checkout.Session.create(
        mode='payment',
        line_items=[
            {
                'price_data': {
                    'currency': payment.currency,
                    'unit_amount': payment.amount_cents,
                    'product_data': {
                        'name': f'Booking fee — appointment with {appointment.doctor}',
                    },
                },
                'quantity': 1,
            }
        ],
        success_url=f'{settings.SITE_URL}/api/docs/?payment=success',
        cancel_url=f'{settings.SITE_URL}/api/docs/?payment=cancelled',
        metadata={'appointment_id': appointment.pk},
    )
    payment.stripe_session_id = session.id
    payment.save(update_fields=['stripe_session_id', 'updated_at'])
    return payment, session


@extend_schema(tags=['Payments'], exclude=True)
class StripeWebhookView(APIView):
    """Receives Stripe events; marks the payment paid on checkout completion."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        signature = request.headers.get('Stripe-Signature', '')
        try:
            event = stripe.Webhook.construct_event(
                request.body, signature, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.SignatureVerificationError):
            return Response(
                {'detail': 'Invalid payload or signature.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            updated = Payment.objects.filter(
                stripe_session_id=session['id'], status=Payment.Status.PENDING
            ).update(status=Payment.Status.PAID)
            if not updated:
                # Unknown or already-paid session: acknowledge so Stripe stops retrying.
                return Response({'received': True, 'matched': False})

        return Response({'received': True})
