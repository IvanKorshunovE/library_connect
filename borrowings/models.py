from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from books.models import Book
from borrowings.telegram_notification import send_to_telegram


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
