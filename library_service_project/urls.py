from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/books/", include("book.urls", namespace="book")),
    path("__debug__/", include("debug_toolbar.urls")),
]
