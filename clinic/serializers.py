from django.utils import timezone
from rest_framework import serializers

from .models import Appointment, Doctor, Patient


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['id', 'first_name', 'last_name', 'specialty', 'is_active', 'created_at']


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'created_at']


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.StringRelatedField(source='doctor', read_only=True)
    patient_name = serializers.StringRelatedField(source='patient', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'doctor', 'doctor_name', 'patient', 'patient_name',
            'scheduled_at', 'status', 'reason', 'created_at', 'updated_at',
        ]

    def validate_scheduled_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError('Appointment must be scheduled in the future.')
        return value

    def validate(self, attrs):
        doctor = attrs.get('doctor', getattr(self.instance, 'doctor', None))
        scheduled_at = attrs.get('scheduled_at', getattr(self.instance, 'scheduled_at', None))
        if doctor and scheduled_at:
            clash = Appointment.objects.filter(
                doctor=doctor, scheduled_at=scheduled_at
            ).exclude(status=Appointment.Status.CANCELLED)
            if self.instance:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise serializers.ValidationError(
                    {'scheduled_at': 'This doctor already has an appointment at this time.'}
                )
        return attrs
