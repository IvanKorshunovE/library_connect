from django.conf import settings
from django.db import models

from books.models import Book


class BorrowingManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(actual_return_date=None)


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
