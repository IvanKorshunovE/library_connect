from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        PAID = "PAID", _("Paid")

    class Type(models.TextChoices):
        PAYMENT = "PAYMENT", _("Payment")
        FINE = "FINE", _("Fine")

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
    )
    type = models.CharField(
        max_length=10,
        choices=Type.choices,
    )
    borrowing = models.ForeignKey(
        'borrowings.Borrowing',
        on_delete=models.CASCADE,
        related_name="payments"
    )
    session_url = models.URLField(
        max_length=250
    )
    session_id = models.CharField(
        max_length=100
    )
    money_to_pay = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    def change_payment_status_to_paid(self):
        self.status = "PAID"
        self.save()

    def __str__(self):
        return (
            f"Status: "
            f"{self.get_status_display()}"
        )
