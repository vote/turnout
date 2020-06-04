from django.urls import include, path

app_name = "api"
urlpatterns = [
    path("registration/", include("register.api_urls")),
    path("absentee/", include("absentee.api_urls")),
    path("verification/", include("verifier.api_urls")),
    path("election/", include("election.api_urls")),
    path("official/", include("official.api_urls")),
    path("storage/", include("storage.api_urls")),
    path("event/", include("event_tracking.api_urls")),
    path("subscriber/", include("multi_tenant.api_urls")),
    path("smsbot/", include("smsbot.api_urls")),
    path("fax/", include("fax.api_urls")),
]
