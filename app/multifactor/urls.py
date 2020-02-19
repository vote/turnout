from django.urls import path

from multifactor import views

app_name = "multifactor"
urlpatterns = [
    path("totp/qrcode/<slug:pk>/", views.TOTPQRCodeView.as_view(), name="totp_qrcode",),
    path("", views.TOTPVerifyView.as_view(), name="authform",),
]
