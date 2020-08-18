import logging

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.timezone import now
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)
from reversion.views import RevisionMixin

from accounts.models import Invite
from common.enums import ExternalToolType
from manage.mixins import ManageViewMixin

from .forms import (
    API_KEY_PLACEHOLDER,
    AssociationManageDeleteForm,
    ChangeSubscriberManageForm,
    InviteAssociationManageDeleteForm,
    InviteCreateForm,
    SubscriberSettingsForm,
)
from .invite import invite_user
from .mixins_manage_views import SubscriberManageViewMixin
from .models import Association, InviteAssociation, SubscriberIntegrationProperty

logger = logging.getLogger("multi_tenant")


class EmbedCodeSampleView(SubscriberManageViewMixin, TemplateView):
    template_name = "multi_tenant/manage/embed.html"


class SubscriberUpdateSettingsView(
    SuccessMessageMixin, SubscriberManageViewMixin, RevisionMixin, UpdateView
):
    form_class = SubscriberSettingsForm
    template_name = "multi_tenant/manage/settings.html"
    success_message = "Subscriber settings have been updated"
    success_url = reverse_lazy("manage:home_redirect")

    def get_actionnetwork_key(self, subscriber):
        return SubscriberIntegrationProperty.objects.filter(
            subscriber=subscriber,
            external_tool=ExternalToolType.ACTIONNETWORK,
            name="api_key",
        ).first()

    def get_object(self):
        return self.subscriber

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["form"].initial["sms_mode"] = data["form"].instance.get_sms_mode()

        old_key = self.get_actionnetwork_key(data["form"].instance)
        if old_key:
            data["form"].initial["sync_actionnetwork"] = True
            data["form"].initial["actionnetwork_api_key"] = API_KEY_PLACEHOLDER

        return data

    def form_valid(self, form):
        form.instance.set_sms_mode(form.cleaned_data.pop("sms_mode"))

        an = form.cleaned_data.pop("sync_actionnetwork", False)
        an_key = form.cleaned_data.pop("actionnetwork_api_key", None)
        old_key = self.get_actionnetwork_key(form.instance)
        if an:
            if an_key and an_key != API_KEY_PLACEHOLDER:
                if old_key:
                    if old_key.value != an_key:
                        old_key.value = an_key
                        old_key.save()
                else:
                    SubscriberIntegrationProperty.objects.create(
                        subscriber=form.instance,
                        external_tool=ExternalToolType.ACTIONNETWORK,
                        name="api_key",
                        value=an_key,
                    )
        else:
            if old_key:
                old_key.delete()

        return super().form_valid(form)


class ChangeSubscriberView(ManageViewMixin, FormView):
    form_class = ChangeSubscriberManageForm
    template_name = "multi_tenant/manage/change_subscriber_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.multi_client_admin:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_form(self):
        form = super().get_form()
        # Explicitly set the choices by changing the queryset of the "subscriber"
        # field. Django will validate that the submission is inside of this
        # queryset.
        form.fields["subscriber"].queryset = self.request.user.allowed_clients.order_by(
            "name"
        )
        return form

    def form_valid(self, form):
        new_client = form.cleaned_data["subscriber"]
        self.request.user.active_client = new_client
        self.request.user.save(update_fields=["active_client"])
        return HttpResponseRedirect(reverse("manage:home", args=[new_client.slug]))


class ManagerListView(
    SubscriberManageViewMixin, ListView,
):
    model = Association
    context_object_name = "associations"
    template_name = "multi_tenant/manage/managers_list.html"

    def get_queryset(self):
        return super().get_queryset().filter(client=self.subscriber)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invite_associations"] = (
            InviteAssociation.objects.filter(client=self.subscriber)
            .exclude(user__user__isnull=False)
            .order_by("-user__expires")
        )
        return context


class ManagerDeleteView(SuccessMessageMixin, SubscriberManageViewMixin, DeleteView):
    model = Association
    context_object_name = "association"
    template_name = "multi_tenant/manage/managers_remove.html"
    form_class = AssociationManageDeleteForm
    success_message = "Manager has been removed from your account."

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(client=self.subscriber)
            .exclude(user=self.request.user)
        )

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = self.object.user
        if user.active_client == self.subscriber:
            user.active_client = None
            user.save()
        self.object.delete()

        extra = {
            "subscriber_uuid": self.subscriber.pk,
            "user_uuid": user.pk,
            "manager_uuid": self.request.user.pk,
        }
        logger.info(
            "User Management: %(manager_uuid)s removed %(user_uuid)s from subscriber %(subscriber_uuid)s",
            extra,
            extra=extra,
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("manage:multi_tenant:manager_list", args=(self.subscriber.slug,))


class ManagerInviteView(SuccessMessageMixin, SubscriberManageViewMixin, CreateView):
    model = Invite
    template_name = "multi_tenant/manage/invite_create.html"
    form_class = InviteCreateForm
    success_message = "%(email)s has been invited"

    def form_valid(self, form):
        invite_user(form.cleaned_data["email"], self.subscriber)

        extra = {
            "subscriber_uuid": self.subscriber.pk,
            "invitee_email": form.cleaned_data["email"],
            "manager_uuid": self.request.user.pk,
        }
        logger.info(
            "User Management: %(manager_uuid)s invited %(invitee_email)s to subscriber %(subscriber_uuid)s",
            extra,
            extra=extra,
        )

        messages.success(self.request, self.success_message % form.cleaned_data)

        return HttpResponseRedirect(
            reverse("manage:multi_tenant:manager_list", args=(self.subscriber.slug,))
        )


class ManagerInviteDeleteView(
    SuccessMessageMixin, SubscriberManageViewMixin, DeleteView
):
    model = InviteAssociation
    context_object_name = "association"
    template_name = "multi_tenant/manage/invite_remove.html"
    form_class = InviteAssociationManageDeleteForm
    success_message = "Invite has been removed from your account."

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(client=self.subscriber)
            .filter(user__user__isnull=True)
        )

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        invite = self.object.user

        # This step will delete the association
        self.object.delete()

        # This will check to see if any associations are left
        if invite.clients.exists():
            # If any association is left, and this subscriber was the primary
            # client, set the invite's client to the first one
            if invite.primary_client == self.subscriber:
                invite.primary_client = invite.clients.first()
                invite.save()
        else:
            # The easiest way to stop an invite from working is to expire it
            invite.expires = now()
            invite.save()
        extra = {
            "subscriber_uuid": self.subscriber.pk,
            "invitee_email": invite.email,
            "manager_uuid": self.request.user.pk,
        }
        logger.info(
            "User Management: %(manager_uuid)s un-invited %(invitee_email)s to subscriber %(subscriber_uuid)s",
            extra,
            extra=extra,
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("manage:multi_tenant:manager_list", args=(self.subscriber.slug,))
