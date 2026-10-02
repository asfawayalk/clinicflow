from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions

from .serializers import RegisterSerializer, UserSerializer


@extend_schema(tags=['Auth'])
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(tags=['Auth'])
class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
