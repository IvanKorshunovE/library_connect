from django.urls import path
from rest_framework import routers

from payments.views import (
    SuccessView,
    CancelView,
    PaymentViewSet,
)

router = routers.DefaultRouter()

router.register("", PaymentViewSet)

urlpatterns = [
    path("success/", SuccessView.as_view(), name="success"),
    path("cancel/", CancelView.as_view(), name="cancel"),
] + router.urls

app_name = "payments"
