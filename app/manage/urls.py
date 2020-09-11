from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import include, path

from manage import views

app_name = "manage"
urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="management/auth/password_reset_form.html",
            success_url="done",
            from_email=f"VoteAmerica <{settings.DEFAULT_EMAIL_FROM}>",
            subject_template_name="management/auth/password_reset_subject.txt",
            email_template_name="management/auth/password_reset_email.html",
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="management/auth/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "password_reset_confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="management/auth/password_reset_confirm.html",
            success_url="/manage/password_reset_complete/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "password_reset_complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="management/auth/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
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
    path("<slug:subscriber>/", include("apikey.manage_urls")),
    path("", views.RedirectToSubscriberManageView.as_view(), name="home_redirect"),
]
