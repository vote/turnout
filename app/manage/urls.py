from django.urls import include, path

from manage import views

app_name = "manage"
urlpatterns = [
    path("login/", views.LoginView.as_view()),
    path("election/", include("election.manage_urls")),
    path("verifier/", include("verifier.manage_urls")),
    path("", views.ManageView.as_view(), name="home"),
]
