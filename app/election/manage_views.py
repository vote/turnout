from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, ListView, TemplateView, UpdateView
from reversion.views import RevisionMixin

from manage.mixins import ManageViewMixin

from .forms import StateInformationManageForm
from .models import State, StateInformation, StateInformationFieldType


class ElectionView(TemplateView):
    template_name = "election/manage/election.html"


class StateListView(ManageViewMixin, ListView):
    model = State
    context_object_name = "states"
    template_name = "election/manage/state_list.html"
    ordering = ["name"]


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


class FieldInformationTypeListView(ManageViewMixin, ListView):
    model = StateInformationFieldType
    context_object_name = "fieldtypes"
    template_name = "election/manage/stateinformationfieldtype_list.html"


class FieldInformationTypeDetailView(ManageViewMixin, DetailView):
    model = StateInformationFieldType
    context_object_name = "fieldtype"
    template_name = "election/manage/stateinformationfieldtype_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["state_information"] = (
            StateInformation.objects.select_related()
            .filter(field_type=kwargs["object"])
            .order_by("state__name")
        )

        return context


class StateInformationUpdateView(ManageViewMixin, RevisionMixin, UpdateView):
    model = StateInformation
    queryset = StateInformation.objects.select_related()
    context_object_name = "state_information"
    template_name = "election/manage/stateinformation_update.html"
    form_class = StateInformationManageForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["field_format"] = self.object.field_type.field_format
        return kwargs

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
            state__pk=self.kwargs["state_code"],
            field_type__slug=self.kwargs["field_slug"],
        )

    def get_success_url(self):
        if self.request.GET.get("ref") == "fieldinformationtype":
            return reverse(
                "manage:election:fieldinformationtype",
                args=[self.object.field_type.slug],
            )
        return reverse("manage:election:state", args=[self.object.state.pk])
