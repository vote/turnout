from django.urls import path

from storage import api_views

app_name = "storage_api"
urlpatterns = [
    path("reset/", api_views.ResetView.as_view(), name="reset"),
    path("secure_upload/", api_views.SecureUploadView.as_view(), name="secure_upload"),
]
