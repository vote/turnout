from django.http import Http404


class EsignAdminView:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_esign:
            raise Http404
        return super().dispatch(request, *args, **kwargs)
