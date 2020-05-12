from django.urls import path

from accounts import manage_profile_views

app_name = "profile"
urlpatterns = [
    path(
        "change_partner/",
        manage_profile_views.ChangePartnerListView.as_view(),
        name="change_partner_list",
    ),
    path(
        "change_partner/<slug:partner_slug>/",
        manage_profile_views.ChangePartnerView.as_view(),
        name="change_partner",
    ),
]
