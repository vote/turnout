from django.urls import path

from subscription import views

app_name = "subscribe"
urlpatterns = [
    path("", views.RegisterView.as_view(), name="register"),
    path("thanks/", views.RegisterThanksView.as_view(), name="register_thanks"),
]
