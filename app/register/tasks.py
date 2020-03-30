from celery import shared_task

from common.analytics import statsd

from .generateform import process_registration
from .models import Registration


@shared_task
@statsd.timed("turnout.register.process_registration_submission")
def process_registration_submission(registration_pk, state_id_number, is_18_or_over):
    registration = Registration.objects.select_related().get(pk=registration_pk)
    process_registration(registration, state_id_number, is_18_or_over)
