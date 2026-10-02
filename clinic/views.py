from django.conf import settings
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from accounts.models import Profile

from .models import Appointment, Doctor, Patient, Payment
from .payments import create_checkout_session
from .permissions import IsReceptionist, IsReceptionistOrReadOnly, get_role
from .serializers import AppointmentSerializer, DoctorSerializer, PatientSerializer


@extend_schema(tags=['Doctors'])
class DoctorViewSet(viewsets.ModelViewSet):
    """Doctors are visible to any authenticated user; only receptionists manage them."""

    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsReceptionistOrReadOnly]


@extend_schema(tags=['Patients'])
class PatientViewSet(viewsets.ModelViewSet):
    """Receptionists manage all patients; doctors may read; a patient sees only their own record."""

    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsReceptionistOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        role = get_role(self.request.user)
        if role == Profile.Role.PATIENT:
            return qs.filter(user=self.request.user)
        return qs


@extend_schema(tags=['Appointments'])
@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'status',
                str,
                enum=[choice[0] for choice in Appointment.Status.choices],
                description='Filter by appointment status.',
            ),
            OpenApiParameter('doctor', int, description='Filter by doctor id.'),
        ]
    )
)
class AppointmentViewSet(viewsets.ModelViewSet):
    """
    Receptionists see and manage all appointments. A patient sees their own and may
    book for themselves. A doctor sees appointments assigned to them.
    """

    queryset = Appointment.objects.select_related('doctor', 'patient')
    serializer_class = AppointmentSerializer

    def get_permissions(self):
        # Changing or deleting an appointment is receptionist-only;
        # listing, retrieving, and booking are open to all roles (filtered below).
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsReceptionist()]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        role = get_role(self.request.user)
        if role == Profile.Role.PATIENT:
            qs = qs.filter(patient__user=self.request.user)
        elif role == Profile.Role.DOCTOR:
            qs = qs.filter(doctor__user=self.request.user)
        status = self.request.query_params.get('status')
        doctor_id = self.request.query_params.get('doctor')
        if status:
            qs = qs.filter(status=status)
        if doctor_id:
            qs = qs.filter(doctor_id=doctor_id)
        return qs

    def perform_create(self, serializer):
        role = get_role(self.request.user)
        if role == Profile.Role.PATIENT:
            patient = getattr(self.request.user, 'patient_record', None)
            if patient is None or serializer.validated_data['patient'] != patient:
                raise PermissionDenied('Patients can only book appointments for themselves.')
        elif role == Profile.Role.DOCTOR:
            raise PermissionDenied('Doctors cannot book appointments.')
        serializer.save()

    @extend_schema(
        request=None,
        responses={200: {'type': 'object', 'properties': {'checkout_url': {'type': 'string'}}}},
        description='Create a Stripe Checkout session for this appointment\'s booking fee.',
    )
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        appointment = self.get_object()
        if not settings.STRIPE_SECRET_KEY:
            return Response(
                {'detail': 'Payments are not configured on this server.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        existing = getattr(appointment, 'payment', None)
        if existing and existing.status == Payment.Status.PAID:
            return Response(
                {'detail': 'This appointment is already paid.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        payment, session = create_checkout_session(appointment)
        return Response({'checkout_url': session.url})
