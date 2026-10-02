from django.urls import path
from rest_framework.routers import DefaultRouter

from .payments import StripeWebhookView
from .views import AppointmentViewSet, DoctorViewSet, PatientViewSet

router = DefaultRouter()
router.register('doctors', DoctorViewSet)
router.register('patients', PatientViewSet)
router.register('appointments', AppointmentViewSet)

urlpatterns = router.urls + [
    path('stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
]
