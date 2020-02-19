from django.urls import path

from accounts import views

app_name = "accounts"
urlpatterns = [
    path(
        "register/<slug:slug>/",
        views.InviteConsumeFormView.as_view(),
        name="consume_invite",
    ),
    path(
        "register/<slug:slug>/success/",
        views.InviteConsumeThanksView.as_view(),
        name="consume_invite_success",
    ),
]
