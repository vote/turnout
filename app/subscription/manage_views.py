from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect
from django.template.defaultfilters import slugify
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from common import enums
from manage.mixins import ManageViewMixin
from multi_tenant.models import Client

from .forms import (
    ActivateInterestForm,
    RejectInterestForm,
    SubscriberAdminSettingsForm,
    SubscriptionAdminSettingsForm,
)
from .mixins_manage_views import SubscriptionAdminView
from .models import Interest, Subscription


class SubscribersListView(ManageViewMixin, SubscriptionAdminView, ListView):
    queryset = Client.objects.select_related("default_slug")
    context_object_name = "subscribers"
    template_name = "subscription/manage/subscriber_list.html"
    ordering = ["name"]


class SubscriberUpdateView(ManageViewMixin, SubscriptionAdminView, UpdateView):
    form_class = SubscriberAdminSettingsForm
    template_name = "subscription/manage/subscriber_edit.html"
    success_url = reverse_lazy("manage:home_redirect")
    context_object_name = "subscriber"

    def get_object(self):
        return get_object_or_404(
            Client, default_slug__slug=self.kwargs["subscriber_slug"]
        )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["form"].initial["sms_mode"] = data["form"].instance.get_sms_mode()
        return data

    def form_valid(self, form):
        form.instance.set_sms_mode(form.cleaned_data.pop("sms_mode"))
        return super().form_valid(form)


class SubscriptionUpdateView(ManageViewMixin, SubscriptionAdminView, UpdateView):
    form_class = SubscriptionAdminSettingsForm
    template_name = "subscription/manage/subscription_edit.html"
    success_url = reverse_lazy("manage:subscription:list_subscribers")
    context_object_name = "subscription"

    def get_object(self):
        return get_object_or_404(
            Subscription, subscriber__default_slug__slug=self.kwargs["subscriber_slug"]
        )


class InterestListView(ManageViewMixin, SubscriptionAdminView, ListView):
    queryset = Interest.objects.filter(
        status=enums.SubscriptionInterestStatus.PENDING
    ).select_related("product")
    context_object_name = "interests"
    template_name = "subscription/manage/interest_list.html"
    ordering = ["status", "organization_name"]


class InterestsDetailView(ManageViewMixin, SubscriptionAdminView, DetailView):
    model = Interest
    context_object_name = "interest"
    template_name = "subscription/manage/interest_detail.html"
    slug_field = "uuid"


class InterestActivateView(
    SuccessMessageMixin, ManageViewMixin, SubscriptionAdminView, CreateView
):
    model = Client
    form_class = ActivateInterestForm
    template_name = "subscription/manage/interest_activate.html"
    success_url = reverse_lazy("manage:subscription:list_interests")
    success_message = "Subscription activated!"

    def dispatch(self, request, *args, **kwargs):
        self.interest = get_object_or_404(Interest, pk=kwargs["pk"])
        if self.interest.consumed:
            messages.warning(
                request, f"This lead has already been activated",
            )
            return redirect("manage:subscription:list_interests")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["interest"] = self.interest
        return context

    def get_initial(self):
        return {
            "name": self.interest.organization_name,
            "initial_user": self.interest.email,
            "url": self.interest.website,
            "slug": slugify(self.interest.organization_name),
        }

    def form_valid(self, form):
        response = super().form_valid(form)
        self.interest.consume(
            subscriber=self.object,
            initial_user_email=form.cleaned_data["initial_user"],
            slug=form.cleaned_data["slug"],
        )
        return response


class InterestRejectView(
    SuccessMessageMixin, ManageViewMixin, SubscriptionAdminView, UpdateView
):
    model = Interest
    object_name = "interest"
    form_class = RejectInterestForm
    template_name = "subscription/manage/interest_reject.html"
    success_url = reverse_lazy("manage:subscription:list_interests")
    success_message = "Subscription rejected!"

    def dispatch(self, request, *args, **kwargs):
        interest = get_object_or_404(Interest, pk=kwargs["pk"])
        if interest.consumed:
            messages.warning(
                request, f"This lead has already been activated",
            )
            return redirect("manage:subscription:list_interests")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.status = enums.SubscriptionInterestStatus.REJECTED
        response = super().form_valid(form)

        return response
