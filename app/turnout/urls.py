from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

from .api_routes import router

urlpatterns = [
    path("-/", include("django_alive.urls")),
    path("v1/", include(router.urls)),
    path(
        "manage/admin/login/",
        RedirectView.as_view(url="/manage/login/", query_string=True),
    ),
    path(
        "manage/admin/logout/",
        RedirectView.as_view(url="/manage/logout/", query_string=True),
    ),
    path("manage/admin/", admin.site.urls),
    path("manage/", include("manage.urls", namespace="manage")),
    path("account/", include("accounts.urls", namespace="accounts")),
]
