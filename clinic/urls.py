from rest_framework.routers import DefaultRouter

from .views import AppointmentViewSet, DoctorViewSet, PatientViewSet

router = DefaultRouter()
router.register('doctors', DoctorViewSet)
router.register('patients', PatientViewSet)
router.register('appointments', AppointmentViewSet)

urlpatterns = router.urls
