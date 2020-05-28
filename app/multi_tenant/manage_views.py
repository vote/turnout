import logging

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.timezone import now
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    TemplateView,
)

from accounts.models import Invite, User, expire_date_time
from manage.mixins import ManageViewMixin

from .forms import (
    AssociationManageDeleteForm,
    ChangeSubscriberManageForm,
    InviteAssociationManageDeleteForm,
    InviteCreateForm,
)
from .mixins_manage_views import SubscriberManageViewMixin
from .models import Association, InviteAssociation
from .tasks import send_invite_notifcation

logger = logging.getLogger("multi_tenant")


class EmbedCodeSampleView(SubscriberManageViewMixin, ManageViewMixin, TemplateView):
    template_name = "multi_tenant/manage/embed.html"


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
        form.fields["subscriber"].queryset = self.request.user.allowed_clients
        return form

    def form_valid(self, form):
        new_client = form.cleaned_data["subscriber"]
        self.request.user.active_client = new_client
        self.request.user.save(update_fields=["active_client"])
        return HttpResponseRedirect(reverse("manage:home", args=[new_client.slug]))


class ManagerListView(
    SubscriberManageViewMixin, ManageViewMixin, ListView,
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


class ManagerDeleteView(
    SuccessMessageMixin, SubscriberManageViewMixin, ManageViewMixin, DeleteView
):
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


class ManagerInviteView(
    SuccessMessageMixin, SubscriberManageViewMixin, ManageViewMixin, CreateView
):
    model = Invite
    template_name = "multi_tenant/manage/invite_create.html"
    form_class = InviteCreateForm
    success_message = "Your invite to %(email)s has been sent."

    def form_valid(self, form):
        # Handle an existing user
        try:
            existing_user = User.objects.get(email__iexact=form.cleaned_data["email"])
            # If the existing user is client-less, make that user a member of this client
            if existing_user.active_client == None:
                existing_user.active_client = self.subscriber
            # Add the user to this subscriber
            existing_user.clients.add(self.subscriber)
            existing_user.save()
            messages.success(self.request, f"User {existing_user} has been added.")

            extra = {
                "subscriber_uuid": self.subscriber.pk,
                "user_uuid": existing_user.pk,
                "manager_uuid": self.request.user.pk,
            }
            logger.info(
                "User Management: %(manager_uuid)s added %(user_uuid)s to subscriber %(subscriber_uuid)s",
                extra,
                extra=extra,
            )

            return HttpResponseRedirect(
                reverse(
                    "manage:multi_tenant:manager_list", args=(self.subscriber.slug,)
                )
            )
        except User.DoesNotExist:
            pass

        # Handle a user with a pending invite in the system
        existing_invite = Invite.actives.filter(
            email__iexact=form.cleaned_data["email"]
        ).first()
        if existing_invite:
            # Add the current subscriber. This will automatically dedupe
            existing_invite.clients.add(self.subscriber)
            # Change the invite's primary subscriber to the current one.
            existing_invite.primary_client = self.subscriber
            # Reset the expiration time
            existing_invite.expires = expire_date_time()
            existing_invite.save()

            extra = {
                "subscriber_uuid": self.subscriber.pk,
                "invitee_email": existing_invite.email,
                "manager_uuid": self.request.user.pk,
            }
            logger.info(
                "User Management: %(manager_uuid)s re-invited %(invitee_email)s to subscriber %(subscriber_uuid)s",
                extra,
                extra=extra,
            )

            messages.success(
                self.request,
                f"Invite {existing_invite.email} has been added or updated.",
            )

            return HttpResponseRedirect(
                reverse(
                    "manage:multi_tenant:manager_list", args=(self.subscriber.slug,)
                )
            )

        # Handle a user new to the system
        invite = form.save(commit=False)
        # Set the primary client as this subscriber
        invite.primary_client = self.subscriber
        invite.save()
        invite.clients.add(self.subscriber)

        send_invite_notifcation.delay(invite.pk, self.subscriber.pk)

        messages.success(self.request, self.success_message % form.cleaned_data)

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

        return HttpResponseRedirect(
            reverse("manage:multi_tenant:manager_list", args=(self.subscriber.slug,))
        )


class ManagerInviteDeleteView(
    SuccessMessageMixin, SubscriberManageViewMixin, ManageViewMixin, DeleteView
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
