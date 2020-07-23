from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import InterestForm
from .models import Interest, Product
from .tasks import notify_slack_interest


class RegisterView(CreateView):
    model = Interest
    context_object_name = "registration"
    template_name = "subscription/register.html"
    success_url = reverse_lazy("subscribe:register_thanks")
    form_class = InterestForm

    def get_form(self):
        form = super().get_form()
        if Product.objects.exists():
            form.fields["product"].empty_label = None
            form.fields[
                "product"
            ].widget.choices.field.initial = Product.objects.first()
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        notify_slack_interest.delay(form.instance.pk)
        return response


class RegisterThanksView(TemplateView):
    template_name = "subscription/register_thanks.html"
