import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, mixins
from rest_framework.response import Response
from rest_framework.views import APIView

from borrowings.models import Borrowing
from borrowings.views import GenericViewSet
from payments.models import Payment
from payments.serializers import (
    PaymentListSerializer,
    PaymentSuccessSerializer
)

stripe.api_key = settings.STRIPE_SECRET_KEY

PAYMENT_DOES_NOT_EXIST_RESPONSE = Response(
    {
        "message": "Payment does not exist"
    },
    status=status.HTTP_204_NO_CONTENT
)


class SuccessView(APIView):
    def get(self, request):
        """
        After a successful payment, the user is redirected to this endpoint.
        If the payment status is 'paid', the book inventory will be
        decreased by 1, and the payment status will be updated from
        'pending' to 'paid'. In the case of fine payment,
        the book inventory will be increased by 1.
        """
        session_id = self.request.query_params.get(
            "session_id"
        )
        context = {
            "session_id": session_id
        }
        serializer = PaymentSuccessSerializer(
            context=context
        )
        response_data = serializer.return_success_response()
        message = response_data.get("message")
        status_ = response_data.get("status")
        headers = response_data.get("headers")
        return Response(
            message,
            status=status_,
            headers=headers
        )


class PaymentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    queryset = Payment.objects.select_related(
        "borrowing__user",
        "borrowing__book"
    )
    serializer_class = PaymentListSerializer

    def get_queryset(self):
        queryset = self.queryset
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                borrowing__user=self.request.user
            )
        return queryset


class CancelView(APIView):
    def get(self, request):
        """
        After the canceled payment, the user is
        redirected to this endpoint.
        """
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
    """
    This webhook does not do anything,
    but it can extend functionality
    if necessary
    """
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
    return HttpResponse(status=200)
