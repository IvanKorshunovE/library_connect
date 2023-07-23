from _decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from books.models import Book
from borrowings.models import Borrowing
from borrowings.tests.test_create_list_return_borrowings_api import sample_user, sample_book
from payments.models import Payment


SESSION_ID = "test_id"

def session_(**params):
    session = {
        "metadata": {
            "is_fine_payment": False
        },
        "payment_status": "paid"
    }
    session.update(params)
    return session


User = get_user_model()


class SuccessViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            **sample_user()
        )
        self.book = Book.objects.create(
            **sample_book()
        )
        self.borrowing = Borrowing.objects.create(
            expected_return_date=datetime.now(),
            book=self.book,
            user=self.user,
        )
        self.payment = Payment.objects.create(
            status="PENDING",
            type="PAYMENT",
            borrowing=self.borrowing,
            session_url="https://stackoverflow.com/",
            session_id=SESSION_ID,
            money_to_pay=Decimal('10.99')
        )
        self.success_url = reverse("payments:success")

    @patch(
        "stripe.checkout.Session.retrieve",
        return_value=session_()
    )
    def test_success_payment(self, mock_retrieve):
        book = self.book
        book_starting_inventory = book.inventory
        borrowing = self.borrowing
        payment = self.payment
        response = self.client.get(
            self.success_url,
            {"session_id": SESSION_ID}
        )
        payment.refresh_from_db()
        borrowing.refresh_from_db()
        book.refresh_from_db()

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            payment.status,
            "PAID"
        )
        self.assertEqual(
            book.inventory,
            book_starting_inventory - 1,
        )
        self.assertEqual(
            borrowing.actual_return_date,
            datetime.now().date()
        )
        self.assertEqual(
            response.headers.get("payment_type"),
            "borrowing_payment"
        )

    @patch(
        "stripe.checkout.Session.retrieve",
        return_value=session_(
            metadata={
                "is_fine_payment": True
            }
        )
    )
    def test_success_fine_payment(self, mock_retrieve):
        book = self.book
        book_starting_inventory = book.inventory
        borrowing = self.borrowing
        session_id = "test_id"
        payment = Payment.objects.create(
            status="PENDING",
            type="PAYMENT",
            borrowing=borrowing,
            session_url="https://stackoverflow.com/",
            session_id=session_id,
            money_to_pay=Decimal('10.99')
        )

        response = self.client.get(
            self.success_url,
            {"session_id": session_id}
        )
        payment.refresh_from_db()
        borrowing.refresh_from_db()
        book.refresh_from_db()

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            payment.status,
            "PAID"
        )
        self.assertEqual(
            book.inventory,
            book_starting_inventory + 1,
        )
        self.assertEqual(
            borrowing.actual_return_date,
            datetime.now().date()
        )
        self.assertEqual(
            response.headers.get("payment_type"),
            "fine_payment"
        )
