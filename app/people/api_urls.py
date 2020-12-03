from django.urls import path

from .api_views import OptOutView

app_name = "api_people"
urlpatterns = [
    path("opt-out/", OptOutView.as_view()),
]
