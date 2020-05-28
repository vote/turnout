from django.urls import path

from multi_tenant import manage_views

app_name = "multi_tenant"
urlpatterns = [
    path("embed/", manage_views.EmbedCodeSampleView.as_view(), name="embed_code"),
    path("users/", manage_views.ManagerListView.as_view(), name="manager_list"),
    path(
        "users/<slug:pk>/remove/",
        manage_views.ManagerDeleteView.as_view(),
        name="manager_remove",
    ),
    path(
        "invite/create/",
        manage_views.ManagerInviteView.as_view(),
        name="invite_create",
    ),
    path(
        "invite/<slug:pk>/remove/",
        manage_views.ManagerInviteDeleteView.as_view(),
        name="invite_remove",
    ),
]
