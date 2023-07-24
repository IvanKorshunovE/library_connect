from _decimal import Decimal
from datetime import datetime

import stripe
from rest_framework import status
from rest_framework.response import Response

from borrowings.models import Borrowing
from payments.helper_borrowing_function import (
    create_stripe_session,
)
from payments.models import Payment


def change_payment_status_to_paid(payment):
    payment.status = "PAID"
    payment.save()


def make_today_actual_return_date(borrowing: Borrowing):
    borrowing.actual_return_date = datetime.now().date()
    borrowing.save()


def decrease_book_inventory(borrowing: Borrowing):
    book = borrowing.book
    book.inventory -= 1
    book.save()


def increase_book_inventory(borrowing: Borrowing):
    book = borrowing.book
    book.inventory += 1
    book.save()


def fine_coefficient(expected_price: Decimal) -> Decimal:
    return expected_price * Decimal("2")


def calculate_fine_price(borrowing: Borrowing) -> Decimal:
    book = borrowing.book
    daily_fee = book.daily_fee
    time_difference = (
            datetime.now().date()
            - borrowing.expected_return_date
    )
    time_difference = time_difference.days
    expected_price = daily_fee * time_difference
    final_price = fine_coefficient(expected_price)
    return final_price


def check_overdue(borrowing: Borrowing, request):
    today = datetime.now().date()
    expected_return_date = borrowing.expected_return_date
    if today > expected_return_date:
        fine_decimal_price = calculate_fine_price(borrowing)
        checkout_session = create_stripe_session(
            borrowing=borrowing,
            request=request,
            fine_decimal_price=fine_decimal_price
        )
        return checkout_session
    return


def finish_fine_payment(payment):
    borrowing = payment.borrowing
    book = borrowing.book

    make_today_actual_return_date(borrowing)
    increase_book_inventory(borrowing)
    headers = {
        "payment_type": "fine_payment"
    }
    return Response(
        {
            "message":
                f"The book {book.title} has been returned."
        },
        status=status.HTTP_200_OK,
        headers=headers
    )


def payment_successful_response_message(
        borrowing: Borrowing,
        payment: Payment
):
    book = borrowing.book
    start_date = borrowing.borrow_date
    end_date = borrowing.expected_return_date
    formatted_start_date = start_date.strftime(
        "%d %B %Y"
    )
    formatted_end_date = end_date.strftime(
        "%d %B %Y"
    )
    headers = {
        "payment_type": "borrowing_payment"
    }
    return Response(
        {
            "message":
                f"Payment is successful.<br><br>"
                f"Thank you for your purchase!<br><br>"
                f"You can now show this confirmation to a library "
                f"staff and they will give you a book.<br><br>"
                f"Payment ID: {payment.id}<br>"
                f"Payment status: {payment.get_status_display()}<br><br>"
                f"Book: {book.title}\n"
                f"You can use your book staring from "
                f"{formatted_start_date} to {formatted_end_date}.<br><br>"
                f"Have a nice day!"
        },
        status=status.HTTP_201_CREATED,
        headers=headers
    )


def get_payment(session_id):
    return Payment.objects.get(
        session_id=session_id
    )
