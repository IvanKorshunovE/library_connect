from django.test import TestCase

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from users.serializers import (
    CreateUserSerializer,
    UpdateUserSerializer
)


User = get_user_model()
USER_CREATE_URL = reverse("users:user-create")
USER_PROFILE_URL = reverse("users:manage")


def sample_user(**params):
    defaults = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "test_password",
        }
    defaults.update(params)

    return defaults


class UserViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user(self):
        response = self.client.post(
            USER_CREATE_URL,
            data=sample_user()
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        user = User.objects.get(
            email=sample_user()["email"]
        )
        serializer = CreateUserSerializer(user)
        self.assertEqual(
            serializer.data,
            response.data
        )


class ManageUserViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            **sample_user()
        )
        self.client = APIClient()
        self.client.force_authenticate(
            user=self.user
        )

    def test_retrieve_user(self):
        response = self.client.get(USER_PROFILE_URL)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK
        )
        self.assertEqual(
            response.data,
            UpdateUserSerializer(self.user).data
        )

    def test_update_user(self):
        updated_data = {
            "first_name": "Vince",
            "last_name": "Smith",
        }
        response = self.client.patch(
            USER_PROFILE_URL,
            data=updated_data,
        )
        self.assertEqual(
            response.status_code, status.HTTP_200_OK
        )

        updated_data = sample_user(
            **updated_data
        )
        response = self.client.put(
            USER_PROFILE_URL,
            data=updated_data,
        )
        self.assertEqual(
            response.status_code, status.HTTP_200_OK
        )
        self.user.refresh_from_db()
        self.assertEqual(
            self.user.first_name,
            updated_data["first_name"]
        )
        self.assertEqual(
            self.user.last_name,
            updated_data["last_name"]
        )
