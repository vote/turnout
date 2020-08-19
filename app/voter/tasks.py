import datetime
import logging

from celery import shared_task
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from action.models import Action
from common.apm import tracer
from common.rollouts import get_feature, get_feature_int
from smsbot.models import Number
from verifier.alloy import ALLOY_STATES_ENABLED, query_alloy
from verifier.targetsmart import query_targetsmart

from .models import Voter

logger = logging.getLogger("voter")


@tracer.wrap()
def lookup(item):
    # alloy
    alloy_id = None
    alloy_match = None
    if item.state_id in ALLOY_STATES_ENABLED:
        alloy = query_alloy(
            {
                "first_name": item.first_name,
                "last_name": item.last_name,
                "address1": item.address1,
                "address2": item.address2,
                "city": item.city,
                "state": item.state_id,
                "zipcode": item.zipcode,
                "date_of_birth": item.date_of_birth,
            }
        )
        if (
            alloy
            and not alloy.get("error")
            and "data" in alloy
            and alloy["data"]["registration_status"]
        ):
            alloy_match = alloy.get("data")
            logger.info(alloy_match)
            if alloy_match["registration_status"] == "Active":
                alloy_id = alloy_match["alloy_person_id"]

    # targetsmart
    vbid = None
    ts = query_targetsmart(
        {
            "first_name": item.first_name,
            "last_name": item.last_name,
            "address1": item.address1,
            "address2": item.address2,
            "city": item.city,
            "state": item.state_id,
            "zipcode": item.zipcode,
            "date_of_birth": item.date_of_birth,
        }
    )
    for ts_match in ts.get("result_set", []):
        vbid = ts_match.get("vb.voterbase_id")
        break

    # add future voterfile lookups here...

    # link
    if vbid or alloy_id:
        if item.phone:
            number, _ = Number.objects.get_or_create(phone=item.phone,)
        else:
            number = None

        voter = None

        if vbid and not voter:
            try:
                voter = Voter.objects.get(ts_voterbase_id=vbid, state=item.state)
            except ObjectDoesNotExist:
                pass
        if alloy_id and not voter:
            try:
                voter = Voter.objects.get(ts_voterbase_id=alloy_id, state=item.state)
            except ObjectDoesNotExist:
                pass

        if not voter:
            voter = Voter.objects.create(
                ts_voterbase_id=vbid, alloy_person_id=alloy_id, state=item.state,
            )
            logger.info(f"Matched new {voter} from action {item}")
        else:
            logger.info(f"Matched existing {voter} from action {item}")

        if vbid:
            if voter.ts_voterbase_id:
                if voter.ts_voterbase_id != vbid:
                    logger.warning(
                        f"{voter} ts_voterbase_id {voter.ts_voterbase_id} -> {vbid}"
                    )
            else:
                logger.info(f"Expanded {voter} match to include TS voterbase")
            voter.ts_voterbase_id = vbid

        if alloy_id:
            if voter.alloy_person_id:
                if voter.alloy_person_id != alloy_id:
                    logger.warning(
                        f"{voter} alloy_person_id {voter.alloy_person_id} -> {alloy_id}"
                    )
            else:
                logger.info(f"Expanded {voter} match to include alloy")
            voter.alloy_person_id = alloy_id

        if number:
            if voter.phone and voter.phone != number:
                logger.warning(f"Changed {voter} number {voter.phone} -> {number}")
            voter.phone = number
        if item.email:
            if voter.email and voter.email != item.email:
                logger.warning(f"Changed {voter} email {voter.email} -> {item.email}")
            voter.email = item.email

        # refresh voter info
        if vbid:
            voter.refresh_status_from_ts(ts_match)
            if not alloy_id:
                voter.refresh_pii_from_ts(ts_match)
        if alloy_id:
            voter.refresh_status_from_alloy(alloy_match)
            voter.refresh_pii_from_alloy(alloy_match)
        voter.save()

        if item.action.voter != voter:
            item.action.voter = voter

    item.action.last_voter_lookup = datetime.datetime.now(tz=datetime.timezone.utc)
    item.action.save()


@shared_task
def check_new_actions(limit=None, state=None):
    if limit is None:
        limit = get_feature_int("voter_action_check", "max_check")
        if not limit:
            logger.info("voter_action_check disabled or max_check==0")
            return
    if limit is None:
        limit = settings.VOTER_CHECK_MAX
    logger.info(f"check_new_actions limit {limit}")
    query = Action.objects.filter(last_voter_lookup=None)
    if state:
        query = query.filter(
            Q(lookup__state_id=state)
            | Q(registration__state_id=state)
            | Q(ballotrequest__state_id=state)
            | Q(reminderrequest__state_id=state)
        )
    query = query.order_by("created_at")
    if limit:
        query = query[:limit]
    for action in query:
        item = action.get_source_item()
        if item:
            lookup(item)


@shared_task
def recheck_old_actions(limit=None):
    if limit is None:
        limit = get_feature_int("voter_action_check", "max_recheck")
        if not limit:
            logger.info("voter_action_check disabled or max_recheck==0")
            return
    if limit is None:
        limit = settings.VOTER_CHECK_MAX
    logger.info(f"recheck_old_actions limit {limit}")
    lookup_cutoff = datetimex.appdatetime.now(
        tz=datetime.timezone.utc
    ) - datetime.timedelta(days=settings.VOTER_RECHECK_INTERVAL_DAYS)
    action_cutoff = datetime.datetime.now(
        tz=datetime.timezone.utc
    ) - datetime.timedelta(days=settings.VOTER_RECHECK_MAX_DAYS)
    query = (
        Action.objects.filter(last_voter_lookup__isnull=False)
        .filter(last_voter_lookup__lt=lookup_cutoff)
        .filter(created_at__gt=action_cutoff)
    )
    if state:
        query = query.filter(
            Q(lookup__state_id=state)
            | Q(registration__state_id=state)
            | Q(ballotrequest__state_id=state)
            | Q(reminderrequest__state_id=state)
        )
    query = query.order_by("created_at")
    if limit:
        query = query[:limit]
    for action in query:
        item = action.get_source_item()
        if item:
            lookup(item)


@shared_task
def voter_lookup_action(pk):
    if not get_feature("voter_action_check"):
        logger.info("voter_action_check disabled")
        return
    action = Action.objects.get(uuid=pk)
    item = action.get_source_item()
    if item:
        lookup(item)
