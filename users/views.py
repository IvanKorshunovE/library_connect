from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated

from users.serializers import (
    CreateUserSerializer,
    UpdateUserSerializer,
    ChangePasswordSerializer,
)


class UserViewSet(
    CreateAPIView
):
    queryset = get_user_model().objects.all()
    serializer_class = CreateUserSerializer


class ManageUserView(
    generics.RetrieveUpdateAPIView
):
    serializer_class = UpdateUserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    queryset = get_user_model().objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        response = super().put(request, *args, **kwargs)
        user = self.get_object()
        if hasattr(user, "password_changed") and user.password_changed:
            response.data["message"] = "Password changed"

        return response
