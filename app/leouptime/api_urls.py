from django.urls import path

from . import api_views

urlpatterns = [
    path("sites-down/", api_views.SiteDownList.as_view()),
    path("sites-blocked/", api_views.SiteBlockedList.as_view()),
    path("sites/", api_views.SiteList.as_view(), name="site-list"),
    path("sites/<str:pk>/", api_views.SiteDetail.as_view(), name="site-detail"),
    path("sites/<str:pk>/checks/", api_views.SiteChecksList.as_view()),
    path("sites/<str:pk>/downtime/", api_views.SiteDowntimeList.as_view()),
    path("checks/<str:pk>/", api_views.SiteCheckDetail.as_view(), name="check-detail"),
    path("downtime/", api_views.DowntimeList.as_view()),
]
