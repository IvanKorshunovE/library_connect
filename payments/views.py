from datetime import datetime

import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from borrowings.helper_functions import (
    decrease_book_inventory,
    increase_book_inventory, make_today_actual_return_date
)
from borrowings.models import Borrowing
from borrowings.telegram_notification import send_to_telegram
from payments.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


class SuccessView(APIView):
    def get(self, request):
        session_id = self.request.query_params.get(
            "session_id"
        )
        session = stripe.checkout.Session.retrieve(
            session_id
        )
        is_fine_payment = session["metadata"]["is_fine_payment"]
        payment_status = session["payment_status"]
        paid = payment_status == "paid"
        if paid:
            try:
                payment = Payment.objects.get(
                    session_id=session_id
                )
                payment.status = "PAID"
                payment.save()

                if is_fine_payment:
                    borrowing = payment.borrowing
                    book = borrowing.book

                    make_today_actual_return_date(borrowing)
                    increase_book_inventory(borrowing)

                    return Response(
                        {
                            "message":
                                f"The book {book.title} has been returned."
                        },
                        status=status.HTTP_200_OK
                    )

                borrowing = payment.borrowing
                book = payment.borrowing.book

                decrease_book_inventory(borrowing)

                start_date = borrowing.borrow_date
                end_date = borrowing.expected_return_date
                formatted_start_date = start_date.strftime(
                    "%d %B %Y"
                )
                formatted_end_date = end_date.strftime(
                    "%d %B %Y"
                )
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
                    }
                )
            except Payment.DoesNotExist as e:
                print("Payment does not exist")
                raise e
        return Response(
            {
                "message":
                    f"Payment status: {payment_status}"
            }
        )


class CancelView(APIView):
    def get(self, request):
        return Response(
            {
                "message":
                    (
                        "Payment can be made later. "
                        "The session is available for 24 hours."
                    )
            }
        )


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = stripe.checkout.Session.retrieve(
            event["data"]["object"]["id"],
            expand=["line_items"],
        )
        borrowing_id = session["metadata"]["borrowing_id"]
        borrowing = Borrowing.objects.get(
            id=borrowing_id
        )
        send_to_telegram("PURCHASED")
    return HttpResponse(status=200)
