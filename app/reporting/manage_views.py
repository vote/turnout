from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.views.generic import CreateView

from manage.mixins import ManageViewMixin
from multi_tenant.mixins_manage_views import PartnerGenericViewMixin

from .forms import ReportCreationForm
from .models import Report
from .tasks import process_report


class ReportCreateView(
    SuccessMessageMixin, PartnerGenericViewMixin, ManageViewMixin, CreateView
):
    model = Report
    template_name = "reporting/manage/report_create.html"
    form_class = ReportCreationForm
    success_message = "Report is being generated and will be emailed to you."

    def get_success_url(self):
        return reverse("manage:home", args=[self.kwargs["partner"]])

    def form_valid(self, form):
        """Handle a valid form"""
        form.instance.author = self.request.user
        form.instance.partner = self.partner

        response = super().form_valid(form)

        process_report.delay(self.object.pk)

        return response
