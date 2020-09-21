from django.urls import path

from absentee import manage_region_ovbm_views

app_name = "absentee_region_ovbm"
urlpatterns = [
    path(
        "",
        manage_region_ovbm_views.RegionOVBMLinkListView.as_view(),
        name="region_ovbm_link_list",
    ),
    path(
        "new",
        manage_region_ovbm_views.RegionOVBMLinkCreateView.as_view(),
        name="region_ovbm_link_create",
    ),
    path(
        "<slug:pk>/edit",
        manage_region_ovbm_views.RegionOVBMLinkUpdateView.as_view(),
        name="region_ovbm_link_update",
    ),
    path(
        "<slug:pk>/delete",
        manage_region_ovbm_views.RegionOVBMLinkDeleteView.as_view(),
        name="region_ovbm_link_delete",
    ),
]
