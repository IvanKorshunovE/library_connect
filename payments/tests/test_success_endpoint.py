from _decimal import Decimal
from datetime import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from django.urls import reverse

from books.models import Book
from borrowings.models import Borrowing
from borrowings.tests.test_create_list_return_borrowings_api import (
    sample_user, sample_book
)
from payments.models import Payment

SESSION_ID = "test_id"
SUCCESS_URL = reverse("payments:success")


def session_(**params):
    session = {
        "metadata": {
            "is_fine_payment": False
        },
        "payment_status": "paid"
    }
    session.update(params)
    return session


def refresh_data(payment, borrowing, book):
    payment.refresh_from_db()
    borrowing.refresh_from_db()
    book.refresh_from_db()


User = get_user_model()


class SuccessViewTest(TestCase):
    def setUp(self):
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

    def refresh_data(self):
        self.payment.refresh_from_db()
        self.borrowing.refresh_from_db()
        self.book.refresh_from_db()

    @patch(
        "stripe.checkout.Session.retrieve",
        return_value=session_()
    )
    def test_success_payment(self, mock_retrieve):
        """
        This test checks the behaviour of success
        endpoint if session has status 'paid', and
        "is_fine_payment": False parameter in metadata.
        """
        book = self.book
        book_starting_inventory = book.inventory
        borrowing = self.borrowing
        payment = self.payment
        response = self.client.get(
            SUCCESS_URL,
            {
                "session_id": SESSION_ID
            }
        )
        self.refresh_data()

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
            None
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
        """
        This test checks the behaviour of success
        endpoint if session has status 'paid' and
        "is_fine_payment": True parameter in metadata.
        """
        book_starting_inventory = self.book.inventory
        response = self.client.get(
            SUCCESS_URL,
            {
                "session_id": SESSION_ID
            }
        )
        self.refresh_data()

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self.payment.status,
            "PAID"
        )
        self.assertEqual(
            self.book.inventory,
            book_starting_inventory + 1,
        )
        self.assertEqual(
            self.borrowing.actual_return_date,
            datetime.now().date()
        )
        self.assertEqual(
            response.headers.get("payment_type"),
            "fine_payment"
        )

    @patch(
        "stripe.checkout.Session.retrieve",
        return_value=session_()
    )
    def test_payment_does_not_exist(self, mock_retrieve):
        """
        This test checks the behaviour of success
        endpoint if the payment related to the
        session is not found.
        """
        book_starting_inventory = self.book.inventory
        self.payment.session_id = "not_exist"
        self.payment.save()
        response = self.client.get(
            SUCCESS_URL,
            {
                "session_id": SESSION_ID
            }
        )
        self.refresh_data()

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertEqual(
            self.payment.status,
            "PENDING"
        )
        self.assertEqual(
            self.book.inventory,
            book_starting_inventory,
        )
        self.assertEqual(
            self.borrowing.actual_return_date,
            None
        )

    @patch(
        "stripe.checkout.Session.retrieve",
        return_value=session_(
            payment_status="not paid"
        )
    )
    def test_session_returns_not_paid(self, mock_retrieve):
        """
        This test examines the behavior of the success
        endpoint when the status of the payment inside
        the session is not "paid."
        """
        response = self.client.get(
            SUCCESS_URL,
            {
                "session_id": SESSION_ID
            }
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
