from django.urls import include, path

from manage import views

app_name = "manage"
urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("profile/", include("accounts.manage_profile_urls")),
    path("election/", include("election.manage_urls")),
    path("absentee_dashboard/", include("absentee.dashboard.manage_urls")),
    path("subscription/", include("subscription.manage_urls")),
    path("<slug:subscriber>/verifier/", include("verifier.manage_urls")),
    path("<slug:subscriber>/register/", include("register.manage_urls")),
    path("<slug:subscriber>/absentee/", include("absentee.manage_urls")),
    path("<slug:subscriber>/reports/", include("reporting.manage_urls")),
    path("<slug:subscriber>/", views.ManageView.as_view(), name="home"),
    path("<slug:subscriber>/", include("multi_tenant.manage_urls")),
    path("", views.RedirectToSubscriberManageView.as_view(), name="home_redirect"),
]
