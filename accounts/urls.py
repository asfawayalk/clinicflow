from django.urls import path
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import MeView, RegisterView

# Group the JWT endpoints under the Auth tag in the API docs.
token_obtain = extend_schema(tags=['Auth'])(TokenObtainPairView)
token_refresh = extend_schema(tags=['Auth'])(TokenRefreshView)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', token_obtain.as_view(), name='token_obtain_pair'),
    path('token/refresh/', token_refresh.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='me'),
]
