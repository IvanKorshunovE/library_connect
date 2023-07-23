# import datetime
# import uuid
# from _decimal import Decimal
#
# from django.test import TestCase
#
# from django.contrib.auth import get_user_model
# from rest_framework import status
# from rest_framework.test import APIClient
# from django.urls import reverse
#
# from books.models import Book
# from borrowings.tests.help_test_functions.help_test_functions import pay
# from payments.helper_borrowing_function import calculate_borrowing_price
# from payments.models import Payment
#
#
# User = get_user_model()
# TODAY_DATE = datetime.datetime.now().date()
#
# BORROWING_LIST_URL = reverse("borrowings:borrowing-list")
#
#
# def sample_user(**params):
#     defaults = {
#         "email": f"test-{uuid.uuid4()}@example.com",
#         "first_name": "John",
#         "last_name": "Doe",
#         "password": "test_password",
#     }
#     defaults.update(params)
#
#     return defaults
#
#
# def sample_book(**params):
#     defaults = {
#         "title": "Win Every Argument",
#         "author": "Mehdi Hasan",
#         "cover": "H",
#         "inventory": 10,
#         "daily_fee": Decimal("1.99")
#     }
#     defaults.update(params)
#
#     return defaults
#
#
# def sample_borrowing(**params):
#     borrow_date = datetime.datetime.now().date()
#     tomorrow = borrow_date + datetime.timedelta(days=1)
#     argument_book = Book.objects.create(
#         **sample_book()
#     )
#     test_user = User.objects.create_user(
#         **sample_user()
#     )
#
#     defaults = {
#         "borrow_date": borrow_date,
#         "expected_return_date": tomorrow,
#         "actual_return_date": "",
#         "book": argument_book.id,
#         "user": test_user.id,
#
#     }
#     defaults.update(params)
#
#     return defaults
#
#
# class CreateBorrowingUnauthorizedUserTest(TestCase):
#     def test_list_borrowing(self):
#         response = self.client.get(
#             BORROWING_LIST_URL
#         )
#         self.assertEqual(
#             response.status_code,
#             status.HTTP_401_UNAUTHORIZED
#         )
#
#     def test_create_borrowing(self):
#         response = self.client.post(
#             BORROWING_LIST_URL,
#             data=sample_borrowing(),
#         )
#         self.assertEqual(
#             response.status_code,
#             status.HTTP_401_UNAUTHORIZED
#         )
#
#
# class CreateBorrowingAuthorizedUserTest(TestCase):
#
#     def setUp(self) -> None:
#         self.client = APIClient()
#         self.user = User.objects.create_user(
#             **sample_user()
#         )
#         self.client.force_authenticate(
#             user=self.user
#         )
#
#     def test_list_borrowing(self):
#         response = self.client.get(
#             BORROWING_LIST_URL
#         )
#         self.assertEqual(
#             response.status_code,
#             status.HTTP_200_OK
#         )
#
#     def test_create_borrowing(self):
#         book = sample_book(title="TEST")
#         book = Book.objects.create(**book)
#         response = self.client.post(
#             BORROWING_LIST_URL,
#             data=sample_borrowing(
#                 book=book.id
#             ),
#         )
#         message = "Checkout session URL retrieved successfully"
#         response_message = response.data.get("message")
#         checkout_session_url = response.data.get(
#             "checkout_session_url"
#         )
#         payment = Payment.objects.get(
#             session_url=checkout_session_url
#         )
#         book = payment.borrowing.book
#
#         self.assertEqual(
#             response.status_code,
#             status.HTTP_302_FOUND
#         )
#         self.assertEqual(
#             message,
#             response_message
#         )
#         self.assertEqual(
#             payment.status,
#             "PENDING"
#         )
#         self.assertEqual(
#             book.inventory,
#             10
#         )
#         self.assertEqual(
#             book.title,
#             "TEST"
#         )
#
#     def test_return_borrowing_without_overdue(self):
#         """
#         Check if book inventory is increased by 1
#         if user has no fines.
#         - If user tries to return book that he have not
#         yet paid for, inventory will not be increased
#         - If user paid for book (the stripe payment process
#         is skipped) inventory is increased by one and
#         actual_return_date is set for today.
#         """
#         book = sample_book(title="Return")
#         book = Book.objects.create(**book)
#         book_starting_inventory = book.inventory
#         response = self.client.post(
#             BORROWING_LIST_URL,
#             data=sample_borrowing(
#                 book=book.id
#             ),
#         )
#         checkout_session_url = response.data.get(
#             "checkout_session_url"
#         )
#         payment = Payment.objects.get(
#             session_url=checkout_session_url
#         )
#         borrowing = payment.borrowing
#
#         self.assertEqual(
#             book.inventory,
#             book_starting_inventory
#         )
#         RETURN_URL = reverse(
#             "borrowings:borrowing-return-borrowing",
#             args=[borrowing.id]
#         )
#
#         response = self.client.post(
#             RETURN_URL,
#         )
#         message = (
#             "The payment for this borrowing could not be found. "
#             "Therefore, you cannot return a book that you have "
#             "not yet paid for."
#         )
#         book.refresh_from_db()
#         self.assertEqual(
#             response.data["message"],
#             message
#         )
#         self.assertEqual(
#             book.inventory,
#             book_starting_inventory
#         )
#         self.assertEqual(
#             borrowing.actual_return_date,
#             None
#         )
#
#         pay(payment)
#
#         response = self.client.post(
#             RETURN_URL,
#         )
#         message = (
#             f"The book {book.title} has been returned."
#         )
#         book.refresh_from_db()
#         borrowing.refresh_from_db()
#
#         self.assertEqual(
#             response.data["message"],
#             message
#         )
#         self.assertEqual(
#             book.inventory,
#             book_starting_inventory + 1
#         )
#         self.assertEqual(
#             borrowing.actual_return_date,
#             TODAY_DATE
#         )
#
#     def test_return_borrowing_with_overdue(self):
#         """
#         Check that if overdue, the stripe
#         session.url should be returned
#         """
#         book = sample_book(
#             title="Return with overdue",
#         )
#         book = Book.objects.create(**book)
#         book_starting_inventory = book.inventory
#         current_date = datetime.datetime.now().date()
#         two_weeks_ago = current_date - datetime.timedelta(weeks=2)
#         week_ago = current_date - datetime.timedelta(weeks=1)
#
#         response = self.client.post(
#             BORROWING_LIST_URL,
#             data=sample_borrowing(
#                 book=book.id,
#             ),
#         )
#         checkout_session_url = response.data.get(
#             "checkout_session_url"
#         )
#         payment = Payment.objects.get(
#             session_url=checkout_session_url
#         )
#
#         borrowing = payment.borrowing
#         borrowing.borrow_date = week_ago
#         borrowing.expected_return_date = two_weeks_ago
#         borrowing.save()
#
#         payment.money_to_pay = calculate_borrowing_price(
#             borrowing
#         )
#         pay(payment)
#
#         RETURN_URL = reverse(
#             "borrowings:borrowing-return-borrowing",
#             args=[borrowing.id]
#         )
#         response = self.client.post(
#             RETURN_URL,
#         )
#         message = (
#             "Successfully retrieved the checkout session "
#             "URL for processing overdue payment"
#         )
#         response_message = response.data.get(
#             "message"
#         )
#         book.refresh_from_db()
#         borrowing.refresh_from_db()
#         self.assertEqual(
#             response_message,
#             message
#         )
#         self.assertEqual(
#             book.inventory,
#             book_starting_inventory
#         )
#         self.assertEqual(
#             borrowing.actual_return_date,
#             None
#         )
