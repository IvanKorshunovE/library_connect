from datetime import datetime

from django.shortcuts import redirect
from rest_framework import generics, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSetMixin

from borrowings.helper_functions import check_overdue
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingSerializer,
    CreateBorrowingSerializer,
    ReadBorrowingSerializer,
    EmptySerializer
)
from payments.helper_borrowing_function import (
    create_stripe_session,
    AmountTooLargeError
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
    queryset = Borrowing.objects.select_related("book")
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Borrowing.objects.select_related("book")
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        is_active = self.request.query_params.get(
            "is_active"
        )
        if is_active:
            queryset = queryset.filter(actual_return_date=None)

        if self.request.user.is_staff:
            user_id = self.request.query_params.get(
                "user_id"
            )
            if user_id:
                queryset = queryset.filter(user_id=user_id)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "create":
            return CreateBorrowingSerializer
        elif self.action in ["list", "retrieve"]:
            return ReadBorrowingSerializer
        elif self.action == "return_borrowing":
            return EmptySerializer

        return BorrowingSerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="return",
        permission_classes=[IsAuthenticated],
    )
    def return_borrowing(self, request, pk=None):
        borrowing = self.get_object()
        if borrowing.actual_return_date:
            raise ValidationError(
                f"The book {borrowing.book} has already been "
                f"returned. You can't return the same "
                f"borrowing twice"
            )

        overdue = check_overdue(borrowing, request)
        if overdue:
            try:
                return redirect(overdue.url)
            except AmountTooLargeError as e:
                raise AmountTooLargeError
            except Exception as e:
                raise e

        borrowing.actual_return_date = datetime.now().date()
        book = borrowing.book
        book.inventory += 1
        borrowing.save()
        book.save()
        return Response(
            {
                "message":
                    f"The book {book.title} has been returned."
            },
            status=status.HTTP_200_OK
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        borrowing = serializer.instance
        checkout_session = create_stripe_session(
            borrowing, request=self.request
        )
        return Response(checkout_session.url)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
