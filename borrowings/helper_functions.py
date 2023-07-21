from _decimal import Decimal
from datetime import datetime


from borrowings.models import Borrowing
from payments.helper_borrowing_function import (
    create_stripe_session,
)


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
