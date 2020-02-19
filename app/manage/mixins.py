from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse


class ManageViewMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        # Only staff can access management pages
        if request.user.is_authenticated and not request.user.is_staff:
            return redirect("/")

        if not request.user.is_verified():
            return redirect(reverse("multifactor:authform"))

        return super(ManageViewMixin, self).dispatch(request, *args, **kwargs)
