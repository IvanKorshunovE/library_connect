from datetime import datetime

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from books.serializers import BookBorrowingSerializer
from borrowings.models import Borrowing
from payments.helper_borrowing_function import create_stripe_session
from payments.serializers import PaymentSerializer


class ReadBorrowingSerializer(serializers.ModelSerializer):
    book = BookBorrowingSerializer(read_only=True)
    payments = PaymentSerializer(read_only=True, many=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "user",
            "borrow_date",
            "expected_return_date",
            "book",
            "actual_return_date",
            "payments"
        )


class CreateBorrowingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Borrowing
        fields = ("expected_return_date", "book")

    def validate_book(self, value):
        """
        Check that the book inventory is more than zero.
        """
        if value.inventory == 0:
            raise serializers.ValidationError(
                f'No "{value.title}" books left'
            )
        return value

    def validate_expected_return_date(self, value):
        """
        Ensure that the user is unable to set
        the return date to a time in the past.
        """
        if value < datetime.now().date():
            raise serializers.ValidationError(
                f"You can't set the return date before today"
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        print("Inside create")
        request = self.context.get("request")
        user = get_user_model().objects.get(
            pk=request.user.pk
        )
        borrowing = Borrowing.objects.create(
            user=user,
            **validated_data
        )
        checkout_session = create_stripe_session(
            borrowing, request=request
        )
        setattr(self, 'checkout_session_url', checkout_session.url)
        return borrowing

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if hasattr(self, 'checkout_session_url'):
            checkout_session_url = {
                "checkout_session_url": self.checkout_session_url
            }
            representation.update(checkout_session_url)
        return representation


class BorrowingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Borrowing
        fields = "__all__"


class EmptySerializer(serializers.Serializer):
    pass
