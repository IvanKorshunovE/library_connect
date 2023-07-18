from rest_framework import serializers

from books.serializers import BookBorrowingSerializer
from borrowings.models import Borrowing


class ReadBorrowingSerializer(serializers.ModelSerializer):
    book = BookBorrowingSerializer(read_only=True)

    class Meta:
        model = Borrowing
        fields = ("borrow_date", "expected_return_date", "book")


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

    def create(self, validated_data):
        """
        If a new Borrowing instance created,
        subtract one book from book.inventory.
        """
        borrowing = Borrowing.objects.create(
            **validated_data
        )
        book = borrowing.book
        book.inventory -= 1
        book.save()
        return borrowing


class BorrowingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Borrowing
        fields = "__all__"
