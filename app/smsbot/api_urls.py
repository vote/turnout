from django.urls import path

from smsbot import api_views

urlpatterns = [
    path("twilio/", api_views.twilio),
    path("twilio-message-status/<str:pk>/", api_views.twilio_message_status),
]
