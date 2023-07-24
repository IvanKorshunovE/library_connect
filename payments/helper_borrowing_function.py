from _decimal import Decimal

import stripe
from rest_framework.exceptions import ValidationError
from stripe.error import InvalidRequestError
from rest_framework.reverse import reverse

from borrowings.models import Borrowing
from payments.models import Payment


class AmountTooLargeError(ValidationError):
    default_detail = (
        "The amount for the "
        "transaction is too large."
    )
    default_code = "amount_too_large"


def calculate_borrowing_price(
        borrowing: Borrowing
) -> Decimal:
    """
    Multiply difference between
    borrowing date and return date
     and calculate Decimal price
    """
    book = borrowing.book
    daily_fee = book.daily_fee
    time_difference = (
            borrowing.expected_return_date
            - borrowing.borrow_date
    )
    time_difference = time_difference.days + 1
    expected_price = daily_fee * time_difference
    return expected_price


def calculate_stripe_price(
        decimal_price: Decimal
) -> int:
    """
    Convert price in USD (Decimal)
    to cents (int) by multiplying it to 100
    """
    stripe_price = decimal_price * Decimal("100")
    stripe_price = int(stripe_price)
    return stripe_price


def create_stripe_session(
        borrowing: Borrowing,
        request,
        fine_decimal_price=None

):
    if fine_decimal_price:
        is_fine_payment = True
        payment_type = Payment.Type.FINE
        stripe_payment = calculate_stripe_price(
            fine_decimal_price
        )
        decimal_price = fine_decimal_price
    else:
        is_fine_payment = ""
        payment_type = Payment.Type.PAYMENT
        decimal_price = calculate_borrowing_price(
            borrowing
        )
        stripe_payment = calculate_stripe_price(
            decimal_price
        )
    book = borrowing.book
    try:
        success_url = request.build_absolute_uri(
            reverse("payments:success")
        )
        cancel_url = request.build_absolute_uri(
            reverse("payments:cancel")
        )

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": stripe_payment,
                        "product_data": {
                            "name": book.title,
                        }
                    },
                    "quantity": 1
                },
            ],
            metadata={
                "borrowing_id": borrowing.id,
                "is_fine_payment": is_fine_payment
            },
            mode="payment",
            success_url=(
                    success_url +
                    "?session_id={CHECKOUT_SESSION_ID}"
            )
            ,
            cancel_url=(
                    cancel_url +
                    "?session_id={CHECKOUT_SESSION_ID}"
            )
        )
        session_url = checkout_session.get("url")
        session_id = checkout_session.get("id")
        Payment.objects.create(
            status=Payment.Status.PENDING,
            type=payment_type,
            borrowing=borrowing,
            session_url=session_url,
            session_id=session_id,
            money_to_pay=decimal_price
        )

        return checkout_session

    except InvalidRequestError as e:
        if "Amount is too large" in str(e):
            raise AmountTooLargeError
    except Exception as e:
        raise e
