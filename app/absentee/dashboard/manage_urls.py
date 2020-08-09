from django.urls import path

from . import manage_views

app_name = "absentee_dashboard"
urlpatterns = [
    path("", manage_views.EsignDashboardView.as_view(), name="esign_dashboard"),
    path(
        "applications/",
        manage_views.BallotRequestListView.as_view(),
        name="esign_application_list",
    ),
    path(
        "applications/<slug:pk>/",
        manage_views.BallotRequestDetailView.as_view(),
        name="esign_application",
    ),
    path(
        "<slug:pk>/",
        manage_views.EsignRegionDashboardView.as_view(),
        name="esign_region_dashboard",
    ),
    path(
        "<slug:state>/<slug:pk>/new",
        manage_views.LeoContactOverrideCreateView.as_view(),
        name="leo_contact_override_create",
    ),
    path(
        "<slug:state>/<slug:pk>/",
        manage_views.LeoContactOverrideDetailView.as_view(),
        name="leo_contact_override_detail",
    ),
    path(
        "<slug:state>/<slug:pk>/edit",
        manage_views.LeoContactOverrideUpdateView.as_view(),
        name="leo_contact_override_update",
    ),
    path(
        "<slug:state>/<slug:pk>/delete",
        manage_views.LeoContactOverrideDeleteView.as_view(),
        name="leo_contact_override_delete",
    ),
]
