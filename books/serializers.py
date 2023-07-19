from rest_framework import serializers

from books.models import Book


class BookSerializer(serializers.ModelSerializer):
    cover = serializers.CharField(source="get_cover_display")

    class Meta:
        model = Book
        fields = "__all__"


class BookBorrowingSerializer(serializers.ModelSerializer):
    """
    A serializer to display book details for a borrower.
    """
    cover = serializers.CharField(source="get_cover_display")

    class Meta:
        model = Book
        exclude = ("inventory", )
