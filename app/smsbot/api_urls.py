from django.urls import path

from smsbot import api_views

urlpatterns = [
    path("twilio/", api_views.twilio),
    path("twilio-message-status/<str:pk>/", api_views.twilio_message_status),
    path("opt-out/", api_views.OptOutView.as_view()),
    path("opt-in/", api_views.OptInView.as_view()),
]
