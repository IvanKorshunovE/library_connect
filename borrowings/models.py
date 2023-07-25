from _decimal import Decimal
from datetime import datetime

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from books.models import Book
from borrowings.helper_functions import fine_coefficient
from borrowings.telegram_notification import send_to_telegram
from payments.helper_borrowing_function import create_stripe_session


class BorrowingManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            actual_return_date=None
        )


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(
        null=True,
        blank=True
    )
    book = models.ForeignKey(
        Book,
        related_name="borrowings",
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="borrowings",
        on_delete=models.CASCADE
    )

    objects = models.Manager()
    is_active = BorrowingManager()

    def make_today_actual_return_date(self):
        self.actual_return_date = datetime.now().date()
        self.save()

    def calculate_fine_price(self) -> Decimal:
        book = self.book
        daily_fee = book.daily_fee
        time_difference = (
                datetime.now().date()
                - self.expected_return_date
        )
        time_difference = time_difference.days
        expected_price = daily_fee * time_difference
        final_price = fine_coefficient(expected_price)
        return final_price

    def calculate_borrowing_price(
            self
    ) -> Decimal:
        """
        Multiply difference between
        borrowing date and return date
         and calculate Decimal price
        """
        book = self.book
        daily_fee = book.daily_fee
        time_difference = (
                self.expected_return_date
                - self.borrow_date
        )
        time_difference = time_difference.days + 1
        expected_price = daily_fee * time_difference
        return expected_price

    def check_overdue(self, request):
        today = datetime.now().date()
        expected_return_date = self.expected_return_date
        if today > expected_return_date:
            fine_decimal_price = self.calculate_fine_price()
            checkout_session = create_stripe_session(
                borrowing=self,
                request=request,
                fine_decimal_price=fine_decimal_price
            )
            return checkout_session
        return

    def __str__(self):
        return f"Borrowing #{self.pk}"


@receiver(post_save, sender=Borrowing)
def my_handler(sender, instance, **kwargs):
    if not instance.actual_return_date:
        message = (
            f"The borrowing #{instance.id} is created, "
            f"expected return date: "
            f"{instance.expected_return_date}"
        )
    else:
        message = (
            f"The borrowing #{instance.id} is returned, "
            f"the actual return date: "
            f"{instance.actual_return_date}"
        )
    send_to_telegram(message)
