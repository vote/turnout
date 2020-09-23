import logging

from celery import shared_task

from absentee.models import BallotRequest
from action.models import Action
from common.rollouts import get_feature_bool
from register.models import Registration
from reminder.models import ReminderRequest
from verifier.models import Lookup

from .actionnetwork import sync, sync_all_items, sync_item
from .models import MoverLead

logger = logging.getLogger("integration")


@shared_task
def sync_lookup_to_actionnetwork(pk: str) -> None:
    sync_item(Lookup.objects.get(uuid=pk))


@shared_task
def sync_ballotrequest_to_actionnetwork(pk: str) -> None:
    sync_item(BallotRequest.objects.get(uuid=pk))


@shared_task
def sync_registration_to_actionnetwork(pk: str) -> None:
    sync_item(Registration.objects.get(uuid=pk))


@shared_task
def sync_reminderrequest_to_actionnetwork(pk: str) -> None:
    sync_item(ReminderRequest.objects.get(uuid=pk))


@shared_task
def sync_action_to_actionnetwork(pk: str) -> None:
    action = Action.objects.get(pk=pk)
    sync_item(action.get_source_item())


@shared_task
def sync_actionnetwork():
    sync()


@shared_task
def sync_actionnetwork_registrations():
    sync_all_items(Registration)


@shared_task
def sync_actionnetwork_lookups():
    sync_all_items(Lookup)


@shared_task
def sync_actionnetwork_ballotrequests():
    sync_all_items(BallotRequest)


@shared_task
def sync_actionnetwork_reminderrequests():
    sync_all_items(ReminderRequest)


@shared_task
def sync_250ok_to_actionnetwork():
    from .actionnetwork import add_test_addrs

    add_test_addrs()


@shared_task
def pull_movers(days=None, hours=None):
    from .movers import pull

    pull(days=days, hours=hours)


@shared_task
def push_movers_to_actionnetwork(limit=None, offset=0, new_state=None) -> None:
    from .movers import push_to_actionnetwork

    push_to_actionnetwork(limit=limit, offset=offset, new_state=new_state)


@shared_task
def geocode_movers(old_state: str = None, new_state: str = None):
    from .movers import geocode_leads

    geocode_leads(old_state=old_state, new_state=new_state)


@shared_task
def sync_movers():
    if get_feature_bool("movers", "pull_movers"):
        pull_movers()
    else:
        logger.info("movers.pull_movers=false")

    if get_feature_bool("movers", "geocode"):
        geocode_movers()
    else:
        logger.info("movers.geocode=false")

    if get_feature_bool("movers", "push_to_actionnetwork"):
        push_movers_to_actionnetwork()
    else:
        logger.info("movers.push_to_actionnetwork=false")


@shared_task
def send_movers_blank_register_forms(lead_pk: str) -> None:
    from .movers import send_blank_register_forms_to_lead

    lead = MoverLead.objects.get(pk=lead_pk)
    send_blank_register_forms_to_lead(lead)


def send_moverlead_mailed(lead_pk: str, action_pk: str) -> None:
    from .notification import trigger_blank_forms_mailed

    lead = MoverLead.objects.get(pk=lead_pk)
    if action_pk == lead.blank_register_forms_action_id:
        trigger_blank_forms_mailed(lead)


def send_moverlead_reminder(lead_pk: str, action_pk: str) -> None:
    from .notification import trigger_blank_forms_reminder

    lead = MoverLead.objects.get(pk=lead_pk)
    if action_pk == lead.blank_register_forms_action_id:
        trigger_blank_forms_reminder(lead)


def send_moverlead_chase(lead_pk: str, action_pk: str) -> None:
    from .notification import trigger_blank_forms_chase

    lead = MoverLead.objects.get(pk=lead_pk)
    if action_pk == lead.blank_register_forms_action_id:
        trigger_blank_forms_chase(lead)
