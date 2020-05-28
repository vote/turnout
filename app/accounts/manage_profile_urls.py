from django.urls import path

from accounts import manage_profile_views
from multi_tenant import manage_views

app_name = "profile"
urlpatterns = [
    path(
        "change_subscriber/",
        manage_views.ChangeSubscriberView.as_view(),
        name="change_subscriber",
    ),
    path(
        "update_profile/",
        manage_profile_views.UpdateProfileView.as_view(),
        name="update_profile",
    ),
    path(
        "change_password/",
        manage_profile_views.UpdatePasswordView.as_view(),
        name="change_password",
    ),
]
