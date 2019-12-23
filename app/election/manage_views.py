from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, ListView, TemplateView, UpdateView
from reversion.views import RevisionMixin

from manage.mixins import ManageViewMixin

from .models import State, StateInformation


class ElectionView(TemplateView):
    template_name = "election/manage/election.html"


class StateListView(ManageViewMixin, ListView):
    model = State
    context_object_name = "states"
    template_name = "election/manage/state_list.html"


class StateDetailView(ManageViewMixin, DetailView):
    model = State
    context_object_name = "state"
    template_name = "election/manage/state_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["state_information"] = StateInformation.objects.select_related().filter(
            state=kwargs["object"]
        )

        return context


class StateInformationUpdateView(ManageViewMixin, RevisionMixin, UpdateView):
    model = StateInformation
    queryset = StateInformation.objects.select_related()
    context_object_name = "state_information"
    template_name = "election/manage/stateinformation_update.html"
    fields = ["text", "notes"]

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
            state__pk=self.kwargs["state_code"],
            field_type__slug=self.kwargs["field_slug"],
        )

    def get_success_url(self):
        return reverse("manage:election:state", args=[self.object.state.pk])
