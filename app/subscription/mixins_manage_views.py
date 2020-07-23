from django.http import Http404


class SubscriptionAdminView:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_subscribers:
            raise Http404
        return super().dispatch(request, *args, **kwargs)
