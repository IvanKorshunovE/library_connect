import stripe
from rest_framework import serializers, status

from books.serializers import BookSerializer
from borrowings.helper_functions import get_payment, finish_fine_payment, payment_successful_response_message
from payments.models import Payment


PAYMENT_DOES_NOT_EXIST_RESPONSE = {
        "message": "Payment does not exist",
        "status": status.HTTP_204_NO_CONTENT
    }


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = "__all__"


class PaymentListSerializer(PaymentSerializer):
    payer_id = serializers.PrimaryKeyRelatedField(
        source="borrowing.user.id",
        read_only=True
    )
    book = BookSerializer(
        source="borrowing.book",
        read_only=True
    )

    class Meta:
        model = Payment
        fields = "__all__"


class PaymentSuccessSerializer(serializers.Serializer):

    def return_success_response(self):
        session_id = self.context.get("session_id")
        session = stripe.checkout.Session.retrieve(
            session_id
        )
        is_fine_payment = session.get(
            "metadata"
        ).get("is_fine_payment")
        payment_status = session.get("payment_status")
        paid = payment_status == "paid"

        if paid:
            try:
                payment = get_payment(session_id)
            except Payment.DoesNotExist as e:
                return PAYMENT_DOES_NOT_EXIST_RESPONSE
            payment.change_payment_status_to_paid()
            if is_fine_payment:
                response = finish_fine_payment(payment)
                return response

            borrowing = payment.borrowing
            borrowing.book.decrease_book_inventory()
            response = payment_successful_response_message(
                payment
            )
            return response
        return {
            "message":
                f"Something went wrong",
            "status": status.HTTP_204_NO_CONTENT,
        }
