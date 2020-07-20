from django.urls import path

from . import views

app_name = "multi_tenant"
urlpatterns = [
    path("signup/", views.signup_view),
]
