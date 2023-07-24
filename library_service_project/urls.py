from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from payments.views import stripe_webhook

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/books/", include("books.urls", namespace="books")),
    path("api/users/", include("users.urls", namespace="users")),
    path("api/borrowings/", include("borrowings.urls", namespace="borrowings")),
    path("api/payments/", include("payments.urls", namespace="payments")),
    path("webhooks/stripe/", stripe_webhook, name="stripe-webhook"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("__debug__/", include("debug_toolbar.urls")),
]
