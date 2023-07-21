from django.urls import path

from payments.views import (
    SuccessView,
    CancelView,
)

urlpatterns = [
    path("success/", SuccessView.as_view(), name="success"),
    path("cancel/", CancelView.as_view(), name="cancel"),
]

app_name = "payments"
