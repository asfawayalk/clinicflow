from django.contrib import admin

from .models import Appointment, Doctor, Patient, Payment


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'specialty', 'is_active']
    list_filter = ['specialty', 'is_active']
    search_fields = ['first_name', 'last_name']


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'phone']
    search_fields = ['first_name', 'last_name', 'email']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'scheduled_at', 'status']
    list_filter = ['status', 'doctor']
    date_hierarchy = 'scheduled_at'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'amount_cents', 'currency', 'status', 'updated_at']
    list_filter = ['status']
