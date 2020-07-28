from django.core.exceptions import ObjectDoesNotExist
from django.views.generic.base import RedirectView
from rest_framework.viewsets import ReadOnlyModelViewSet

from cdn.views_mixin import CDNCachedView

from .models import State, StateInformation, StateInformationFieldType
from .serializers import FieldSerializer, StateFieldSerializer, StateSerializer


class StateViewSet(CDNCachedView, ReadOnlyModelViewSet):
    model = State
    serializer_class = StateSerializer
    queryset = State.objects.all()


class StateFieldsViewSet(CDNCachedView, ReadOnlyModelViewSet):
    model = StateInformationFieldType

    queryset = StateInformationFieldType.objects.all()
    lookup_field = "slug"

    def list(self, request):
        self.serializer_class = FieldSerializer
        return super().list(request)

    def retrieve(self, request, slug=None):
        self.serializer_class = StateFieldSerializer
        return super().retrieve(request, slug)


class StateExternalToolRedirectView(RedirectView):
    permanent = False

    def get_redirect_url(self, state, slug, **kwargs):
        for field in StateInformation.objects.filter(
            state_id=state, field_type__slug=slug
        ):
            if field.text:
                return field.text

        SLUG_FALLBACK_URLS = {
            "external_tool_verify_status": "https://voteamerica.com/am-i-registered-to-vote",
            "external_tool_ovr": "https://voteamerica.com/register-to-vote",
            "external_tool_vbm_application": "https://voteamerica.com/absentee-ballot",
            "external_tool_polling_place": "https://www.voteamerica.com/where-is-my-polling-place",
        }
        if slug in SLUG_FALLBACK_URLS:
            url = SLUG_FALLBACK_URLS[slug]
            try:
                state_obj = State.objects.get(code=state)
                url += "-" + state_obj.url_suffix
            except ObjectDoesNotExist:
                pass
            return url

        return "https://voteamerica.com/"
