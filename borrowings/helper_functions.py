from _decimal import Decimal

from rest_framework import status
from rest_framework.response import Response

from payments.models import Payment


def fine_coefficient(expected_price: Decimal) -> Decimal:
    return expected_price * Decimal("2")


def finish_fine_payment(payment):
    borrowing = payment.borrowing
    book = borrowing.book

    borrowing.make_today_actual_return_date()
    borrowing.book.increase_book_inventory()
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
        borrowing,
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
