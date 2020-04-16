from django.urls import include, path

from manage import views

app_name = "manage"
urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("election/", include("election.manage_urls")),
    path("verifier/", include("verifier.manage_urls")),
    path("register/", include("register.manage_urls")),
    path("absentee/", include("absentee.manage_urls")),
    path("", views.ManageView.as_view(), name="home"),
]
