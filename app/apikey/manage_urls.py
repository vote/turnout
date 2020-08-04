from django.urls import path

from . import manage_views

app_name = "apikey"
urlpatterns = [
    path("keys/", manage_views.ApiKeyListView.as_view(), name="key_list"),
    path(
        "keys/<str:pk>/deactivate/",
        manage_views.ApiKeyDeactivateView.as_view(),
        name="key_deactivate",
    ),
    path("keys/create/", manage_views.ApiKeyCreateView.as_view(), name="key_create",),
]
