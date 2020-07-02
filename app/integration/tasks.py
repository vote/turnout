from celery import shared_task

from .actionnetwork import sync, sync_item


@shared_task
def sync_lookup_to_actionnetwork(pk: str) -> None:
    from verifier.models import Lookup

    sync_item(Lookup.objects.get(uuid=pk))


@shared_task
def sync_ballotrequest_to_actionnetwork(pk: str) -> None:
    from absentee.models import BallotRequest

    sync_item(BallotRequest.objects.get(uuid=pk))


@shared_task
def sync_registration_to_actionnetwork(pk: str) -> None:
    from register.models import Registration

    sync_item(Registration.objects.get(uuid=pk))


@shared_task
def sync_actionnetwork():
    sync()


@shared_task
def sync_uptimedotcom():
    from .uptimedotcom import sync

    sync()
