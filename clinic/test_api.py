import pytest

from clinic.models import Appointment, Patient

FUTURE = '2030-01-15T09:00:00Z'


def book(client, doctor, patient, scheduled_at=FUTURE, **extra):
    return client.post(
        '/api/appointments/',
        {'doctor': doctor.id, 'patient': patient.id, 'scheduled_at': scheduled_at, **extra},
        format='json',
    )


@pytest.mark.django_db
class TestBookingValidation:
    def test_booking_in_the_past_rejected(self, receptionist_client, doctor, patient):
        response = book(receptionist_client, doctor, patient, scheduled_at='2020-01-01T09:00:00Z')
        assert response.status_code == 400
        assert 'scheduled_at' in response.json()

    def test_double_booking_rejected(self, receptionist_client, doctor, patient):
        other = Patient.objects.create(first_name='Other', last_name='One', email='o@x.com')
        assert book(receptionist_client, doctor, patient).status_code == 201
        response = book(receptionist_client, doctor, other)
        assert response.status_code == 400

    def test_cancelled_slot_can_be_rebooked(self, receptionist_client, doctor, patient):
        first = book(receptionist_client, doctor, patient).json()
        receptionist_client.patch(
            f"/api/appointments/{first['id']}/", {'status': 'cancelled'}, format='json'
        )
        assert book(receptionist_client, doctor, patient).status_code == 201

    def test_status_filter(self, receptionist_client, doctor, patient):
        book(receptionist_client, doctor, patient)
        response = receptionist_client.get('/api/appointments/?status=cancelled')
        assert response.json()['count'] == 0
        response = receptionist_client.get('/api/appointments/?status=scheduled')
        assert response.json()['count'] == 1


@pytest.mark.django_db
class TestRolePermissions:
    def test_patient_cannot_manage_doctors(self, patient_client):
        response = patient_client.post(
            '/api/doctors/', {'first_name': 'X', 'last_name': 'Y'}, format='json'
        )
        assert response.status_code == 403

    def test_patient_sees_only_own_record(self, patient_client, patient):
        Patient.objects.create(first_name='Other', last_name='One', email='o@x.com')
        response = patient_client.get('/api/patients/')
        assert response.json()['count'] == 1
        assert response.json()['results'][0]['email'] == patient.email

    def test_patient_books_only_for_self(self, patient_client, doctor, patient):
        other = Patient.objects.create(first_name='Other', last_name='One', email='o@x.com')
        assert book(patient_client, doctor, patient).status_code == 201
        response = book(patient_client, doctor, other, scheduled_at='2030-01-15T10:00:00Z')
        assert response.status_code == 403

    def test_doctor_cannot_book(self, doctor_client, doctor, patient):
        assert book(doctor_client, doctor, patient).status_code == 403

    def test_doctor_sees_only_own_appointments(
        self, receptionist_client, doctor_client, doctor, patient
    ):
        from clinic.models import Doctor

        other_doctor = Doctor.objects.create(first_name='Bob', last_name='Lee')
        book(receptionist_client, doctor, patient)
        book(receptionist_client, other_doctor, patient, scheduled_at='2030-01-15T10:00:00Z')
        assert doctor_client.get('/api/appointments/').json()['count'] == 1

    def test_patient_cannot_edit_appointment(self, patient_client, receptionist_client, doctor, patient):
        appointment = book(patient_client, doctor, patient).json()
        response = patient_client.patch(
            f"/api/appointments/{appointment['id']}/", {'status': 'completed'}, format='json'
        )
        assert response.status_code == 403
        response = receptionist_client.patch(
            f"/api/appointments/{appointment['id']}/", {'status': 'checked_in'}, format='json'
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestConfirmationEmail:
    def test_booking_sends_confirmation_email(
        self, receptionist_client, doctor, patient, mailoutbox, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            book(receptionist_client, doctor, patient)
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == [patient.email]
        assert 'confirmed' in mailoutbox[0].subject
