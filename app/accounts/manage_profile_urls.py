from django.urls import path

from multi_tenant import manage_views

app_name = "profile"
urlpatterns = [
    path(
        "change_subscriber/",
        manage_views.ChangeSubscriberView.as_view(),
        name="change_subscriber",
    ),
]
