from django.urls import path

from smsbot import api_views

urlpatterns = [
    path("twilio/", api_views.twilio),
]
