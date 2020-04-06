from django.urls import path

from register import manage_views

app_name = "register"
urlpatterns = [
    path("", manage_views.RegistrationListView.as_view(), name="registration_list"),
    path(
        "<slug:pk>/",
        manage_views.RegistrationDetailView.as_view(),
        name="registration_detail",
    ),
]
