from django.urls import path

from election import manage_views

app_name = "election"
urlpatterns = [
    path("", manage_views.ElectionView.as_view(), name="main"),
    path("state/", manage_views.StateListView.as_view(), name="state_list"),
    path("state/<slug:pk>/", manage_views.StateDetailView.as_view(), name="state"),
    path(
        "state/<slug:state_code>/<slug:field_slug>/",
        manage_views.StateInformationUpdateView.as_view(),
        name="update_information",
    ),
    path(
        "fieldinformationtype/",
        manage_views.FieldInformationTypeListView.as_view(),
        name="fieldinformationtype_list",
    ),
    path(
        "fieldinformationtype/<slug:slug>/",
        manage_views.FieldInformationTypeDetailView.as_view(),
        name="fieldinformationtype",
    ),
]
