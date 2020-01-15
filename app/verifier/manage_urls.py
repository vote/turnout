from django.urls import path

from verifier import manage_views

app_name = "verifier"
urlpatterns = [
    path("", manage_views.LookupListView.as_view(), name="lookup_list"),
    path("<slug:pk>/", manage_views.LookupDetailView.as_view(), name="lookup_detail"),
]
