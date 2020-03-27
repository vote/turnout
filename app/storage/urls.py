from django.urls import path

from storage import public_views

app_name = "storage"
urlpatterns = [
    path("<slug:pk>/", public_views.DownloadFileView.as_view(), name="download"),
]
