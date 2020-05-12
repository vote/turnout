from django.views.generic import TemplateView

from manage.mixins import ManageViewMixin


class EmbedCodeSampleView(ManageViewMixin, TemplateView):
    template_name = "multi_tenant/manage/embed.html"
