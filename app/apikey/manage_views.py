import logging

from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from multi_tenant.mixins_manage_views import SubscriberManageViewMixin

from .forms import ApiKeyCreateForm, ApiKeyDeactivateForm
from .models import ApiKey

logger = logging.getLogger("apikey")


class ApiAccessViewMixin(SubscriberManageViewMixin):
    def check_subscriber_access(self):
        if not self.subscriber.has_api_access:
            raise Http404


class ApiKeyListView(
    ApiAccessViewMixin, ListView,
):
    model = ApiKey
    context_object_name = "apikeys"
    template_name = "apikey/manage/key_list.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(subscriber=self.subscriber)
            .filter(deactivated_by__isnull=True)
        )


class ApiKeyDeactivateView(SuccessMessageMixin, ApiAccessViewMixin, UpdateView):
    model = ApiKey
    context_object_name = "apikey"
    template_name = "apikey/manage/key_deactivate.html"
    form_class = ApiKeyDeactivateForm
    success_message = "API Key has been deactivated."

    def get_queryset(self):
        return super().get_queryset().filter(subscriber=self.subscriber)

    def form_valid(self, form):
        form.instance.deactivated_by = self.request.user
        form.instance.save()
        extra = {
            "apikey_uuid": form.instance.pk,
            "user_uuid": self.request.user.pk,
            "subscriber_uuid": self.subscriber.pk,
        }
        logger.info(
            "API Key management: %(apikey_uuid)s deactivated by %(user_uuid)s for subscriber %(subscriber_uuid)s",
            extra,
            extra=extra,
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("manage:apikey:key_list", args=(self.subscriber.slug,))


class ApiKeyCreateView(SuccessMessageMixin, ApiAccessViewMixin, CreateView):
    model = ApiKey
    context_object_name = "apikey"
    form_class = ApiKeyCreateForm
    template_name = "apikey/manage/key_create.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.subscriber = self.subscriber
        form.instance.description = form.cleaned_data["description"]
        form.instance.save()

        return render(
            self.request,
            "apikey/manage/key_created.html",
            {
                "uuid": form.instance.uuid,
                "hashed_secret": form.instance.hashed_secret(),
            },
        )
