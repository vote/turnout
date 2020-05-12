from django.urls import path

from multi_tenant import manage_views

app_name = "multi_tenant"
urlpatterns = [
    path("embed/", manage_views.EmbedCodeSampleView.as_view(), name="embed_code"),
]
