from django.http import Http404


class ElectionAdminView:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_election_information:
            raise Http404
        return super().dispatch(request, *args, **kwargs)
