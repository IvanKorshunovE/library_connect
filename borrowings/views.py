from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSetMixin

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingSerializer,
    CreateBorrowingSerializer,
    ReadBorrowingSerializer,
    ReturnBorrowingSerializer
)


class GenericViewSet(ViewSetMixin, generics.GenericAPIView):
    """
    The GenericViewSet class does not provide any actions by default,
    but does include the base set of generic view behavior, such as
    the `get_object` and `get_queryset` methods.
    """
    pass


class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    queryset = (
        Borrowing.objects.select_related(
            "book"
        ).prefetch_related(
            "payments"
        )
    )
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        else:
            user_id = self.request.query_params.get("user_id")
            if user_id:
                queryset = queryset.filter(user_id=user_id)

        is_active = self.request.query_params.get("is_active")
        if is_active:
            is_active = is_active.lower() == "true"
            queryset = queryset.filter(
                actual_return_date=None
            ) if is_active else queryset

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "create":
            return CreateBorrowingSerializer
        elif self.action in ["list", "retrieve"]:
            return ReadBorrowingSerializer
        elif self.action == "return_borrowing":
            return ReturnBorrowingSerializer

        return BorrowingSerializer

    @extend_schema(
        methods=["POST"],
        description=(
                "This endpoint facilitates the process of returning a "
                "borrowed book. When called, it will perform the "
                "following actions based on different scenarios:\n"
                "1. If the book is overdue, the endpoint will return "
                "a Stripe session URL for processing overdue payment, "
                "and it will not alter the book's inventory.\n"
                "2. If the borrowing has no associated payments, "
                "the endpoint will respond with a message indicating "
                "that the payment for the borrowing could not be found. "
                "Additionally, it will not modify the book's inventory.\n"
                "3. If the book has already been returned, the endpoint "
                "will respond with a message stating that the book has "
                "been returned, and it will not make any changes to the "
                "database.\n"
                "4. In the case of a successful book return, the "
                "endpoint will set the return date for today and "
                "increase the inventory count of the related book by 1, "
                "reflecting the returned copy.\n\n"
                "The endpoint aims to handle these scenarios while "
                "ensuring accurate inventory management and appropriate "
                "user communication during the book return process."
        ),
        responses={
            status.HTTP_200_OK: {
                "properties": {
                    "message": {
                        "description":
                            "Message indicating that "
                            "the book has been returned.",
                    },
                }
            },
            status.HTTP_302_FOUND: {
                "properties": {
                    "message": {
                        "description":
                            "Message indicating success "
                            "in retrieving the checkout session URL.",
                    },
                    "checkout_session_url": {
                        "description":
                            "URL for the checkout session "
                            "for overdue payment processing.",
                    },
                },
            },
            status.HTTP_400_BAD_REQUEST: {
                "properties": {
                    "message": {
                        "description":
                            "Error message indicating that payment "
                            "for the borrowing could not be found.",
                    },
                },
            },
        },
    )
    @action(
        methods=["POST"],
        detail=True,
        url_path="return",
        permission_classes=[IsAuthenticated],
    )
    def return_borrowing(self, request, pk=None):
        borrowing = self.get_object()
        context = {
            "borrowing": borrowing,
            "request": self.request
        }
        serializer = self.get_serializer(
            context=context
        )
        response_data = serializer.return_borrowing()
        return Response(response_data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description=(
                        "Filter by active borrowings "
                        "(where actual date is None)."
                        "Type 'true' if you want to use"
                        "this filter, otherwise leave it "
                        "empty or type 'false'"
                ),
                required=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
