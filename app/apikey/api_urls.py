from django.urls import path

from apikey import api_views

app_name = "apikey"
urlpatterns = [
    path("check/", api_views.CheckView.as_view(), name="check",),
]
