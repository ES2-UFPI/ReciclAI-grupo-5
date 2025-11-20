from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("reciclAI.urls", namespace="reciclAI")),
    path("accounts/", include("django.contrib.auth.urls")),
]
