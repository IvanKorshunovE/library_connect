from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView
)

from users.views import (
    UserViewSet,
    ManageUserView,
    ChangePasswordView
)


urlpatterns = [
    path("", UserViewSet.as_view(), name="user-create"),
    path("me/", ManageUserView.as_view(), name="manage"),
    path("me/change_password/", ChangePasswordView.as_view(), name="change_password"),
    path("token/", TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("token/refresh/", TokenRefreshView.as_view(), name='token_refresh'),
]

app_name = "users"
