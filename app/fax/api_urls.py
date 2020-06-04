from django.urls import path

from fax import api_views

app_name = "fax"
urlpatterns = [
    path(
        "gateway_callback/",
        api_views.GatewayCallbackView.as_view(),
        name="gateway_callback",
    ),
]
