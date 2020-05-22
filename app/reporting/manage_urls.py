from django.urls import path

from reporting import manage_views

app_name = "reporting"
urlpatterns = [
    path("create/", manage_views.ReportCreateView.as_view(), name="request"),
]
