from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView
from django_otp.admin import OTPAdminSite

admin.site.__class__ = OTPAdminSite

urlpatterns = [
    path("-/", include("django_alive.urls")),
    path("v1/", include("turnout.api_urls")),
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
    path("multifactor/", include("multifactor.urls", namespace="multifactor")),
    path("download/", include("storage.urls", namespace="storage")),
]
