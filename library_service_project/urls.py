from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/books/", include("books.urls", namespace="books")),
    path("api/users/", include("users.urls", namespace="users")),
    path("api/borrowings/", include("borrowings.urls", namespace="borrowings")),
    path("__debug__/", include("debug_toolbar.urls")),
]
