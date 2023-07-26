import datetime
import uuid
from _decimal import Decimal

from django.test import TestCase

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse

from books.models import Book
from borrowings.tests.help_test_functions.help_test_functions import pay
from payments.models import Payment

User = get_user_model()
TODAY_DATE = datetime.datetime.now().date()

BORROWING_LIST_URL = reverse("borrowings:borrowing-list")
BORROWING_NOT_FOUND_MESSAGE = (
    "The payment for this borrowing could not be found. "
    "Therefore, you cannot return a book that you have "
    "not yet paid for."
)
OVERDUE_PAYMENT_MESSAGE = (
    "Successfully retrieved the checkout session "
    "URL for processing overdue payment"
)


def sample_user(**params):
    defaults = {
        "email": f"test-{uuid.uuid4()}@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password": "test_password",
    }
    defaults.update(params)

    return defaults


def sample_book(**params):
    defaults = {
        "title": "Win Every Argument",
        "author": "Mehdi Hasan",
        "cover": "H",
        "inventory": 10,
        "daily_fee": Decimal("1.99")
    }
    defaults.update(params)

    return defaults


def return_url_(borrowing_id):
    return reverse(
        "borrowings:borrowing-return-borrowing",
        args=[borrowing_id]
    )


def find_payment(checkout_session_url):
    return Payment.objects.get(
        session_url=checkout_session_url
    )


def retrieve_checkout_session_url(response):
    return response.data.get(
        "checkout_session_url"
    )


def book_returned_message(book_title):
    return f"The book {book_title} has been returned."


def sample_borrowing(**params):
    borrow_date = datetime.datetime.now().date()
    tomorrow = borrow_date + datetime.timedelta(days=1)
    argument_book = Book.objects.create(
        **sample_book()
    )
    test_user = User.objects.create_user(
        **sample_user()
    )

    defaults = {
        "borrow_date": borrow_date,
        "expected_return_date": tomorrow,
        "actual_return_date": "",
        "book": argument_book.id,
        "user": test_user.id,

    }
    defaults.update(params)

    return defaults


class CreateBorrowingUnauthorizedUserTest(TestCase):
    def test_list_borrowing(self):
        response = self.client.get(
            BORROWING_LIST_URL
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_create_borrowing(self):
        response = self.client.post(
            BORROWING_LIST_URL,
            data=sample_borrowing(),
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )


class CreateBorrowingAuthorizedUserTest(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            **sample_user()
        )
        self.client.force_authenticate(
            user=self.user
        )
        self.book = Book.objects.create(
            **sample_book()
        )

    def test_list_borrowing(self):
        response = self.client.get(
            BORROWING_LIST_URL
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_create_borrowing(self):
        book_title = self.book.title
        response = self.client.post(
            BORROWING_LIST_URL,
            data=sample_borrowing(
                book=self.book.id
            ),
        )

        checkout_session_url_exists = response.data.get("checkout_session_url")
        if checkout_session_url_exists:
            payment = find_payment(checkout_session_url_exists)
            self.assertEqual(
                payment.status,
                "PENDING"
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertTrue(
            checkout_session_url_exists
        )
        self.assertEqual(
            self.book.inventory,
            10
        )
        self.assertEqual(
            self.book.title,
            book_title
        )

    def test_return_borrowing_without_overdue(self):
        """
        Check if book inventory is increased by 1
        if user has no fines.
        - If user tries to return book that he have not
        yet paid for, inventory will not be increased
        - If user paid for book (the stripe payment process
        is skipped) inventory is increased by one and
        actual_return_date is set for today.
        """
        book_starting_inventory = self.book.inventory
        response = self.client.post(
            BORROWING_LIST_URL,
            data=sample_borrowing(
                book=self.book.id
            ),
        )
        checkout_session_url = retrieve_checkout_session_url(response)
        payment = find_payment(checkout_session_url)
        borrowing = payment.borrowing

        self.book.refresh_from_db()
        self.assertEqual(
            self.book.inventory,
            book_starting_inventory
        )
        return_url = return_url_(borrowing.id)

        self.book.refresh_from_db()
        self.assertEqual(
            self.book.inventory,
            book_starting_inventory
        )
        self.assertEqual(
            borrowing.actual_return_date,
            None
        )

        pay(payment)

        response = self.client.post(
            return_url,
        )
        message = book_returned_message(self.book.title)
        self.book.refresh_from_db()
        borrowing.refresh_from_db()

        self.assertEqual(
            response.data["message"],
            message
        )
        self.assertEqual(
            self.book.inventory,
            book_starting_inventory + 1
        )
        self.assertEqual(
            borrowing.actual_return_date,
            TODAY_DATE
        )

    def test_return_borrowing_with_overdue(self):
        """
        Check that if overdue, the stripe
        session.url should be returned
        """
        book_starting_inventory = self.book.inventory
        current_date = datetime.datetime.now().date()
        two_weeks_ago = current_date - datetime.timedelta(weeks=2)
        week_ago = current_date - datetime.timedelta(weeks=1)

        response = self.client.post(
            BORROWING_LIST_URL,
            data=sample_borrowing(
                book=self.book.id,
            ),
        )
        checkout_session_url = retrieve_checkout_session_url(response)
        payment = find_payment(checkout_session_url)

        borrowing = payment.borrowing
        borrowing.borrow_date = week_ago
        borrowing.expected_return_date = two_weeks_ago
        borrowing.save()

        payment.money_to_pay = borrowing.calculate_borrowing_price()
        pay(payment)

        return_url = return_url_(borrowing.id)
        response = self.client.post(
            return_url,
        )
        message = OVERDUE_PAYMENT_MESSAGE
        response_message = response.data.get(
            "message"
        )
        self.book.refresh_from_db()
        borrowing.refresh_from_db()
        self.assertEqual(
            response_message,
            message
        )
        self.assertEqual(
            self.book.inventory,
            book_starting_inventory
        )
        self.assertEqual(
            borrowing.actual_return_date,
            None
        )

    def test_not_allow_to_create_if_inventory_0(self):
        """
        Verify that borrowing is not allowed
        for a book with an inventory of 0.
        """
        book = Book.objects.create(
            **sample_book(
                inventory=0
            )
        )
        response = self.client.post(
            BORROWING_LIST_URL,
            data=sample_borrowing(
                book=book.id,
            ),
        )
        self.assertEqual(
            response.data,
            {
                "book":
                    [f'No "{book.title}" books left']
            }
        )
