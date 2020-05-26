from django.urls import path

from absentee import manage_override_views

app_name = "absentee_override"
urlpatterns = [
    path(
        "",
        manage_override_views.LeoContactOverrideListView.as_view(),
        name="leo_contact_override_list",
    ),
    path(
        "new",
        manage_override_views.LeoContactOverrideCreateView.as_view(),
        name="leo_contact_override_create",
    ),
    path(
        "<slug:pk>/",
        manage_override_views.LeoContactOverrideDetailView.as_view(),
        name="leo_contact_override_detail",
    ),
    path(
        "<slug:pk>/edit",
        manage_override_views.LeoContactOverrideUpdateView.as_view(),
        name="leo_contact_override_update",
    ),
    path(
        "<slug:pk>/delete",
        manage_override_views.LeoContactOverrideDeleteView.as_view(),
        name="leo_contact_override_delete",
    ),
]
