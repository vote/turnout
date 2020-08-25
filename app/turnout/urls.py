from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic.base import RedirectView
from two_factor.admin import AdminSiteOTPRequired
from two_factor.gateways.twilio.urls import urlpatterns as tf_twilio_urls
from two_factor.urls import urlpatterns as tf_urls

admin.site.__class__ = AdminSiteOTPRequired

# exclude login from tf_urls -- we implement our own /manage/login
tf_urls = ([u for u in tf_urls[0] if u.name != "login"], tf_urls[1])

urlpatterns = [
    re_path(r"", include(tf_urls)),
    re_path(r"", include(tf_twilio_urls)),
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
    path("download/", include("storage.urls", namespace="storage")),
    path("subscribe/", include("subscription.urls", namespace="subscribe")),
]
