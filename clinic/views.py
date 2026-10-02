from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets

from .models import Appointment, Doctor, Patient
from .serializers import AppointmentSerializer, DoctorSerializer, PatientSerializer


@extend_schema(tags=['Doctors'])
class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer


@extend_schema(tags=['Patients'])
class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer


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
    queryset = Appointment.objects.select_related('doctor', 'patient')
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.query_params.get('status')
        doctor_id = self.request.query_params.get('doctor')
        if status:
            qs = qs.filter(status=status)
        if doctor_id:
            qs = qs.filter(doctor_id=doctor_id)
        return qs
