from celery import shared_task

from common.analytics import statsd

from .models import Registration


@shared_task
@statsd.timed("turnout.register.process_registration_submission")
def process_registration_submission(registration_pk, state_id):
    registration = Registration.objects.get(pk=registration_pk)
