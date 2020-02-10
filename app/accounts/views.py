from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import FormView

from common.utils.uuid_slug_mixin import UUIDSlugMixin

from .forms import InviteConsumeForm
from .models import Invite


class InviteConsumeFormView(UUIDSlugMixin, SingleObjectMixin, FormView):
    form_class = InviteConsumeForm
    template_name = "accounts/invite_consume.html"
    model = Invite
    slug_field = "token"
    context_object_name = "invite"
    success_url = "/"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.user:
            return redirect(self.get_success_url())
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.user:
            return redirect(self.get_success_url())
        if self.object.expired:
            raise Http404
        return super().post(request, *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.post(*args, **kwargs)

    def form_valid(self, form):
        user = form.save(commit=False)
        user.active_client = self.object.primary_client
        user.email = self.object.email
        user.is_staff = True
        user.save()

        self.object.consume_invite(user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "accounts:consume_invite_success", kwargs={"slug": self.object.token}
        )


class InviteConsumeThanksView(UUIDSlugMixin, DetailView):
    template_name = "accounts/invite_consume_success.html"
    model = Invite
    queryset = Invite.objects.exclude(user__isnull=True)
    slug_field = "token"
    context_object_name = "invite"
