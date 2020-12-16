from django.urls import path

from subscription import manage_views

app_name = "subscription"
urlpatterns = [
    path("leads/", manage_views.InterestListView.as_view(), name="list_interests"),
    path(
        "leads/<slug:pk>/",
        manage_views.InterestsDetailView.as_view(),
        name="interests_detail",
    ),
    path(
        "leads/<slug:pk>/activate/",
        manage_views.InterestActivateView.as_view(),
        name="interests_activate",
    ),
    path(
        "leads/<slug:pk>/reject/",
        manage_views.InterestRejectView.as_view(),
        name="interests_reject",
    ),
    path(
        "subscribers/",
        manage_views.SubscribersListView.as_view(),
        name="list_subscribers",
    ),
    path(
        "subscribers/<slug:subscriber_slug>/edit/",
        manage_views.SubscriberUpdateView.as_view(),
        name="edit_subscriber",
    ),
    path(
        "subscribers/<slug:subscriber_slug>/edit_subscription/",
        manage_views.SubscriptionUpdateView.as_view(),
        name="edit_subscription",
    ),
]
