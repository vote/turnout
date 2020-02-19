import qrcode
import qrcode.image.svg
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormView
from django_otp import login as otplogin

from common.utils.uuid_slug_mixin import UUIDSlugMixin

from .forms import TokenForm
from .models import UUIDTOTPDevice


class TOTPQRCodeView(LoginRequiredMixin, UUIDSlugMixin, SingleObjectMixin, View):
    model = UUIDTOTPDevice

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)
        if not self.request.user.is_verified():
            queryset = queryset.filter(confirmed=False)
        return queryset

    def get(self, request, *args, **kwargs):
        device = self.get_object()
        img = qrcode.make(device.config_url, image_factory=qrcode.image.svg.SvgImage)
        response = HttpResponse(content_type="image/svg+xml")
        img.save(response)
        return response


class TOTPVerifyView(LoginRequiredMixin, UUIDSlugMixin, SingleObjectMixin, FormView):
    model = UUIDTOTPDevice
    template_name = "multifactor/totp.html"
    context_object_name = "device"
    form_class = TokenForm
    success_url = reverse_lazy("manage:home")

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        device, _ = queryset.get_or_create(user=self.request.user)
        return device

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["device"] = self.object
        return kwargs

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not settings.MULTIFACTOR_ENABLED:
            otplogin(self.request, self.object)
            return redirect(self.get_success_url())

        if self.request.user.is_verified() and self.object.confirmed:
            return redirect(self.get_success_url())
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        if not self.object.confirmed:
            self.object.confirmed = True
            self.object.save()

        otplogin(self.request, self.object)

        return super().form_valid(form)
