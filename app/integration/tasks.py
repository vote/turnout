import logging

from celery import shared_task

from absentee.models import BallotRequest
from action.models import Action
from common.enums import EventType, ExternalToolType
from common.models import DelayedTask
from common.rollouts import get_feature_bool
from event_tracking.models import Event
from multi_tenant.models import Client
from register.models import Registration
from reminder.models import ReminderRequest
from verifier.models import Lookup

from .actionnetwork import sync, sync_all_items, sync_item
from .models import Link, MoverLead

logger = logging.getLogger("integration")


@shared_task(queue="actionnetwork")
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


@shared_task(queue="actionnetwork")
def sync_subscriber_to_actionnetwork(pk: str) -> None:
    from .actionnetwork import sync_subscriber

    subscriber = Client.objects.get(pk=pk)
    sync_subscriber(subscriber)


@shared_task(queue="actionnetwork")
def unsubscribe_phone_from_actionnetwork(phone: str) -> None:
    from .actionnetwork import unsubscribe_phone

    unsubscribe_phone(phone)


@shared_task(queue="actionnetwork")
def resubscribe_phone_to_actionnetwork(phone: str) -> None:
    from .actionnetwork import resubscribe_phone

    resubscribe_phone(phone)


@shared_task
def pull_movers(days=None, hours=None):
    from .movers import pull

    pull(days=days, hours=hours)


@shared_task
def push_movers_to_actionnetwork(limit=None, offset=0, new_state=None) -> None:
    from .movers import push_to_actionnetwork

    push_to_actionnetwork(limit=limit, offset=offset, new_state=new_state)


@shared_task
def geocode_movers(old_state: str = None, new_state: str = None, limit: int = None):
    from .movers import geocode_leads

    geocode_leads(old_state=old_state, new_state=new_state, limit=limit)


@shared_task(queue="geocode")
def geocode_mover(mover_pk: str) -> None:
    from .movers import geocode_lead

    lead = MoverLead.objects.get(pk=mover_pk)
    geocode_lead(lead)


@shared_task(queue="actionnetwork")
def push_mover_to_actionnetwork(mover_pk: str) -> None:
    from .movers import push_lead

    lead = MoverLead.objects.get(pk=mover_pk)
    push_lead(lead)


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


@shared_task(queue="movers")
def send_blank_register_forms_to_lead(lead_pk: str) -> None:
    from .movers import send_blank_register_forms_to_lead

    lead = MoverLead.objects.get(pk=lead_pk)
    send_blank_register_forms_to_lead(lead)


@shared_task
def send_blank_register_forms_tx(offset=0, limit=None) -> None:
    from .movers import send_blank_register_forms_tx

    send_blank_register_forms_tx(offset=offset, limit=limit)


@shared_task
def send_blank_register_forms(offset=0, limit=None, state=None) -> None:
    from .movers import send_blank_register_forms

    send_blank_register_forms(offset=offset, limit=limit, state=state)


@shared_task
def send_movers_blank_register_forms() -> None:
    if get_feature_bool("movers", "blank_forms"):
        send_blank_register_forms()
    else:
        logger.info("movers.blank_forms=false")
    if get_feature_bool("movers", "blank_forms_tx"):
        send_blank_register_forms_tx()
    else:
        logger.info("movers.blank_forms_tx=false")


@shared_task
def send_moverlead_mailed(lead_pk: str, action_pk: str) -> None:
    from .notification import trigger_blank_forms_mailed

    lead = MoverLead.objects.get(pk=lead_pk)
    if action_pk == lead.blank_register_forms_action_id:
        trigger_blank_forms_mailed(lead)


@shared_task
def send_moverlead_reminder(lead_pk: str, action_pk: str) -> None:
    from .notification import trigger_blank_forms_reminder

    lead = MoverLead.objects.get(pk=lead_pk)
    if action_pk == lead.blank_register_forms_action_id:
        trigger_blank_forms_reminder(lead)


@shared_task
def send_moverlead_chase(lead_pk: str, action_pk: str) -> None:
    from .notification import trigger_blank_forms_chase

    lead = MoverLead.objects.get(pk=lead_pk)
    if action_pk == lead.blank_register_forms_action_id:
        trigger_blank_forms_chase(lead)


@shared_task(queue="lob-status-updates")
def process_lob_letter_status(letter_id: str, etype: str) -> None:
    link = (
        Link.objects.filter(external_tool=ExternalToolType.LOB, external_id=letter_id)
        .order_by("created_at")
        .first()
    )
    if not link:
        logger.warning(
            f"Got lob webhook on unknown letter id {letter_id} etype {etype}"
        )
        return
    action = link.action

    event_mapping = {
        "letter.mailed": EventType.LOB_MAILED,
        "letter.processed_for_delivery": EventType.LOB_PROCESSED_FOR_DELIVERY,
        "letter.re-routed": EventType.LOB_REROUTED,
        "letter.returned_to_sender": EventType.LOB_RETURNED,
    }

    item = action.get_source_item()
    if not item:
        logger.warning(
            f"Recieved lob status update on action {action} with not item, {etype}"
        )
        return

    logger.info(f"Received lob status update on {item} of {etype}")

    if etype in event_mapping:
        t = event_mapping[etype]
        if not Event.objects.filter(event_type=t, action=action).exists():
            action.track_event(t)

    event_trigger = {
        "letter.processed_for_delivery": {
            "Registration": [
                ("register.tasks.send_print_and_forward_mailed", 0),
                ("register.tasks.send_mail_chase", 14),
            ],
            "BallotRequest": [
                ("absentee.tasks.send_print_and_forward_mailed", 0),
                ("absentee.tasks.send_mail_chase", 14),
            ],
            "MoverLead": [
                ("integration.tasks.send_moverlead_mailed", 0),
                ("integration.tasks.send_moverlead_reminder", 3),
                ("integration.tasks.send_moverlead_chase", 28),
            ],
        },
        "letter.returned_to_sender": {
            "Registration": [("register.tasks.send_print_and_forward_returned", 0)],
            "BallotRequest": [("absentee.tasks.send_print_and_forward_returned", 0)],
        },
    }

    if etype in event_trigger:
        itype = type(item).__name__
        state = item.new_state if itype == "MoverLead" else item.state.code
        if itype in event_trigger[etype]:
            for task, days in event_trigger[etype][itype]:
                if days:
                    DelayedTask.schedule_days_later_polite(
                        state, days, task, str(item.pk), str(action.pk)
                    )
                else:
                    DelayedTask.schedule_polite(
                        state, task, str(item.pk), str(action.pk)
                    )
