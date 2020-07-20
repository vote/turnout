from django.shortcuts import render

from common import enums

from .forms import SignupForm
from .models import SubscriberLead


def signup_view(request):

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            #
            is_c3 = form.cleaned_data["is_c3"]
            if is_c3:
                status = enums.SubscriberLeadStatus.PENDING_C3_VERIFICATION
            else:
                status = enums.SubscriberLeadStatus.PENDING_PAYMENT
            sub = SubscriberLead.objects.create(
                name=form.cleaned_data["name"],
                url=form.cleaned_data["url"],
                email=form.cleaned_data["email"],
                is_c3=is_c3,
                status=status,
                slug=form.cleaned_data["slug"],
            )

            return render(request, "signup-pending.html", form.cleaned_data)

    # If this is a GET (or any other method) create the default form.
    else:
        form = SignupForm()

    context = {
        "form": form,
    }

    return render(request, "signup.html", context)
