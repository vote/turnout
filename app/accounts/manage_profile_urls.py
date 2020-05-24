from django.urls import path

from multi_tenant import manage_views

app_name = "profile"
urlpatterns = [
    path(
        "change_partner/",
        manage_views.ChangePartnerView.as_view(),
        name="change_partner_list",
    ),
]
