from django.db import models
from django.utils.translation import gettext_lazy as _


class Book(models.Model):
    class Cover(models.TextChoices):
        HARD = "H", _("Hard")
        SOFT = "S", _("Soft")

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=500)
    cover = models.CharField(
        max_length=1,
        choices=Cover.choices,
    )
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    def decrease_book_inventory(self):
        self.inventory -= 1
        self.save()

    def increase_book_inventory(self):
        self.inventory += 1
        self.save()

    def __str__(self):
        return self.title
