from django.urls import path

from .api_views import lob_letter_status

app_name = "api_integration"
urlpatterns = [
    path("lob-letter-status/<str:pk>/", lob_letter_status),
]
