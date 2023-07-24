from rest_framework import serializers

from books.serializers import BookSerializer
from payments.models import Payment


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
