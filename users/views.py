from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated

from users.serializers import UserSerializer


class UserViewSet(
    CreateAPIView
):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer


class ManageUserView(
    generics.RetrieveUpdateAPIView
):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
