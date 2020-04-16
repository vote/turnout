from django.urls import path

from absentee import manage_views

app_name = "absentee"
urlpatterns = [
    path("", manage_views.BallotRequestListView.as_view(), name="ballot_request_list"),
    path(
        "<slug:pk>/",
        manage_views.BallotRequestDetailView.as_view(),
        name="ballot_request_detail",
    ),
]
