# from django.test import TestCase
# from django.contrib.auth import get_user_model
# from rest_framework.test import APIClient
#
# from books.models import Book
# from borrowings.models import Borrowing
# from borrowings.serializers import ReadBorrowingSerializer
# from borrowings.tests.test_create_list_return_borrowings_api import (
#     sample_user,
#     BORROWING_LIST_URL,
#     sample_book
# )
#
# User = get_user_model()
#
#
# class BorrowingQuerysetTest(TestCase):
#     def setUp(self) -> None:
#         self.client = APIClient()
#         self.user = User.objects.create_user(
#             **sample_user()
#         )
#         self.user_2 = User.objects.create_user(
#             **sample_user(
#                 email="user@user.com"
#             )
#         )
#         self.client.force_authenticate(
#             user=self.user
#         )
#
#     def test_list_borrowing_with_query_params_non_admin(self):
#         """
#         Additionally checks that "user_id" query parameter
#         will not change queryset if current user is not
#         admin
#         """
#         book = sample_book(
#             title="Simple book",
#         )
#         book = Book.objects.create(**book)
#         active_borrowing = Borrowing.objects.create(
#             book=book,
#             user=self.user,
#             borrow_date="2023-06-06",
#             expected_return_date="2023-06-06",
#         )
#         inactive_borrowing = Borrowing.objects.create(
#             book=book,
#             user=self.user,
#             borrow_date="2023-06-06",
#             expected_return_date="2023-06-06",
#             actual_return_date="2023-06-06",
#         )
#         active_borrowing = ReadBorrowingSerializer(active_borrowing)
#         inactive_borrowing = ReadBorrowingSerializer(inactive_borrowing)
#
#         user_with_no_borrowings = User.objects.get(
#             email="user@user.com"
#         )
#
#         response = self.client.get(
#             BORROWING_LIST_URL,
#             {
#                 "is_active": "true",
#                 "user_id": user_with_no_borrowings.id
#             }
#         )
#         self.assertIn(
#             active_borrowing.data,
#             response.data
#         )
#         self.assertNotIn(
#             inactive_borrowing.data,
#             response.data
#         )
#
#     def test_list_borrowing_with_query_params_admin(self):
#         self.superuser = User.objects.create_superuser(
#             **sample_user()
#         )
#         self.client.force_authenticate(
#             user=self.superuser
#         )
#         book = sample_book(
#             title="Admin book",
#         )
#         book = Book.objects.create(**book)
#         active_borrowing = Borrowing.objects.create(
#             book=book,
#             user=self.user,
#             borrow_date="2023-09-06",
#             expected_return_date="2023-06-06",
#         )
#         inactive_borrowing = Borrowing.objects.create(
#             book=book,
#             user=self.superuser,
#             borrow_date="2023-06-06",
#             expected_return_date="2023-06-06",
#             actual_return_date="2023-06-06",
#         )
#
#         active_borrowing = ReadBorrowingSerializer(active_borrowing)
#         inactive_borrowing = ReadBorrowingSerializer(inactive_borrowing)
#         response = self.client.get(
#             BORROWING_LIST_URL,
#             {
#                 "user_id": self.user.id
#             }
#         )
#         self.assertIn(
#             active_borrowing.data,
#             response.data
#         )
#         self.assertNotIn(
#             inactive_borrowing.data,
#             response.data
#         )
