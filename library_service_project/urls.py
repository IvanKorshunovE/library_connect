from django.contrib import admin
from django.urls import path, include

from payments.views import stripe_webhook

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/books/", include("books.urls", namespace="books")),
    path("api/users/", include("users.urls", namespace="users")),
    path("api/borrowings/", include("borrowings.urls", namespace="borrowings")),
    path("api/payments/", include("payments.urls", namespace="payments")),
    path("webhooks/stripe/", stripe_webhook, name="stripe-webhook"),
    path("__debug__/", include("debug_toolbar.urls")),
]
