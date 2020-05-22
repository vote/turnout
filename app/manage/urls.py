from django.urls import include, path

from manage import views

app_name = "manage"
urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("profile/", include("accounts.manage_profile_urls")),
    path("election/", include("election.manage_urls")),
    path("<slug:partner>/verifier/", include("verifier.manage_urls")),
    path("<slug:partner>/register/", include("register.manage_urls")),
    path("<slug:partner>/absentee/", include("absentee.manage_urls")),
    path("<slug:partner>/reports/", include("reporting.manage_urls")),
    path("<slug:partner>/", views.ManageView.as_view(), name="home"),
    path("<slug:partner>/", include("multi_tenant.manage_urls")),
    path("", views.RedirectToPartnerManageView.as_view(), name="home_redirect"),
]
