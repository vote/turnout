import datetime
import logging

from celery import shared_task
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from action.models import Action
from common.apm import tracer
from common.rollouts import get_feature, get_feature_bool, get_feature_int
from smsbot.models import Number
from verifier.targetsmart import query_targetsmart

from .models import Voter
from .state import lookup_state

logger = logging.getLogger("voter")


@tracer.wrap()
def lookup(item):
    if type(item).__name__ not in [
        "BallotRequest",
        "Registration",
        "Lookup",
        "ReminderRequest",
    ]:
        return

    # targetsmart
    ts_id = None
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
    for ts_result in ts.get("result_set", []):
        ts_id = ts_result.get("vb.voterbase_id")
        break

    # per-state query?
    state_voter_id, state_result = lookup_state(item)

    # add future voterfile lookups here...

    # link
    if ts_id or state_voter_id:
        if item.phone:
            number, _ = Number.objects.get_or_create(phone=item.phone,)
        else:
            pass

        voter = None

        if ts_id and not voter:
            try:
                voter = Voter.objects.filter(
                    ts_voterbase_id=ts_id, state=item.state
                ).first()
            except ObjectDoesNotExist:
                pass
        if state_voter_id and not voter:
            try:
                voter = Voter.objects.filter(
                    state_voter_id=state_voter_id, state=item.state
                ).first()
            except ObjectDoesNotExist:
                pass

        if not voter:
            voter = Voter.objects.create(
                ts_voterbase_id=ts_id, state_voter_id=state_voter_id, state=item.state,
            )
            logger.info(f"Matched new {voter} from action {item}")
        else:
            logger.info(f"Matched existing {voter} from action {item}")

        # update external links
        if ts_id:
            if voter.ts_voterbase_id:
                if voter.ts_voterbase_id != ts_id:
                    logger.warning(
                        f"{voter} ts_voterbase_id {voter.ts_voterbase_id} -> {ts_id}"
                    )
            else:
                logger.info(f"Expanded {voter} match to include TS voterbase")
            voter.ts_voterbase_id = ts_id

        if state_voter_id:
            if voter.state_voter_id:
                if voter.state_voter_id != state_voter_id:
                    logger.warning(
                        f"{voter} state_voter_id {voter.state_voter_id} -> {state_voter_id}"
                    )
            else:
                logger.info(
                    f"Expanded {voter} match to include {voter.state_voter_id} state_voter_id {state_voter_id}"
                )
            voter.state_voter_id = state_voter_id

        # refresh voter info
        if item.phone:
            if voter.phone and voter.phone != item.phone:
                logger.warning(f"Changed {voter} number {voter.phone} -> {item.phone}")
            voter.phone = item.phone
        if item.email:
            if voter.email and voter.email != item.email:
                logger.warning(f"Changed {voter} email {voter.email} -> {item.email}")
            voter.email = item.email

        # refresh registration
        if ts_id:
            try:
                reg_date = datetime.datetime.strptime(
                    ts_result.get("vb.vf_registration_date"), "%Y%m%d"
                ).replace(tzinfo=datetime.timezone.utc)
                voter.refresh_registration_status(
                    ts_result.get("vb.voterbase_registration_status") == "Registered",
                    reg_date,
                    reg_date,  # we cannot assume this info is any newer than the date they first registered
                )
            except ValueError:
                logger.warning(f"No registration date for {ts_id}: {ts_result}")
            voter.ts_result = ts_result
            voter.last_ts_refresh = datetime.datetime.now(tz=datetime.timezone.utc)

        if state_voter_id:
            voter.last_state_refresh = datetime.datetime.now(tz=datetime.timezone.utc)
            voter.refresh_registration_status(
                state_result.active,
                datetime.datetime(
                    state_result.registration_date.year,
                    state_result.registration_date.month,
                    state_result.registration_date.day,
                    0,
                    0,
                    0,
                    tzinfo=datetime.timezone.utc,
                ),
                voter.last_state_refresh,
            )
            voter.state_result = {k: str(v) for k, v in state_result.__dict__.items()}

        # name
        if ts_id:
            voter.first_name = ts_result.get("vb.tsmart_first_name")
            voter.middle_name = ts_result.get("vb.tsmart_middle_name")
            voter.last_name = ts_result.get("vb.tsmart_last_name")
            voter.suffix = ts_result.get("vb.tsmart_name_suffix")
        elif state_voter_id:
            # NOTE: we assume the first name has no space here...
            names = state_result.full_name.split()
            voter.first_name = names.pop(0)
            voter.last_name = names.pop()
            voter.middle_name = " ".join(names)

        # other PII (prefer state)
        if state_voter_id:
            voter.date_of_birth = state_result.date_of_birth
            voter.address_full = state_result.address
            voter.city = state_result.city
            voter.zipcode = state_result.zipcode
        elif ts_id:
            voter.date_of_birth = datetime.datetime.strptime(
                ts_result.get("vb.voterbase_dob"), "%Y%m%d"
            ).replace(tzinfo=datetime.timezone.utc)
            voter.address_full = ts_result.get("vb.vf_reg_cass_address_full")
            voter.city = ts_result.get("vb.vf_reg_cass_city")
            voter.zipcode = ts_result.get("vb.vf_reg_cass_zip")

        voter.save()

        if item.action.voter != voter:
            item.action.voter = voter

    item.action.last_voter_lookup = datetime.datetime.now(tz=datetime.timezone.utc)
    item.action.save()


@shared_task
def check_new_actions(
    limit: int = None, state: str = None, max_minutes: int = None
) -> None:
    if limit is None:
        limit = get_feature_int("voter_action_check", "max_check")
        if not limit:
            logger.info("voter_action_check disabled or max_check==0")
            return

    if max_minutes is None:
        max_minutes = get_feature_int("voter_action_check", "max_check_minutes") or (
            settings.VOTER_CHECK_INTERVAL_MINUTES // 2
        )

    cutoff = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc
    ) - datetime.timedelta(seconds=settings.ACTION_CHECK_UNFINISHED_DELAY)

    query = Action.objects.filter(last_voter_lookup=None, created_at__lt=cutoff)
    if state:
        query = query.filter(
            Q(lookup__state_id=state)
            | Q(registration__state_id=state)
            | Q(ballotrequest__state_id=state)
            | Q(reminderrequest__state_id=state)
        )
    else:
        # make sure it matches an item that we actually check
        query = query.filter(
            Q(lookup__isnull=False)
            | Q(registration__isnull=False)
            | Q(ballotrequest__isnull=False)
            | Q(reminderrequest__isnull=False)
        )

    logger.info(
        f"check_new_actions limit {limit} of {query.count()}, state {state}, max_minutes {max_minutes}"
    )

    if not max_minutes:
        max_minutes = settings.VOTER_CHECK_INTERVAL_MINUTES

    queue_async = get_feature_bool("voter_action_check", "check_async")
    if not queue_async:
        stop = datetime.datetime.utcnow() + datetime.timedelta(minutes=max_minutes)

    query = query.order_by("created_at")
    if limit:
        query = query[:limit]
    for action in query:
        if queue_async:
            if state == "WI":
                voter_lookup_action.apply_async(
                    args=(str(action.uuid),),
                    expires=(max_minutes * 60),
                    queue=f"voter-wi",
                )
            else:
                voter_lookup_action.apply_async(
                    args=(str(action.uuid),), expires=(max_minutes * 60)
                )
        else:
            item = action.get_source_item()
            if item:
                lookup(item)
            if stop < datetime.datetime.utcnow():
                logger.info(f"Hit max runtime ({max_minutes} minutes)")
                break


@shared_task
def recheck_old_actions(
    limit: int = None,
    state: str = None,
    min_check_interval: int = None,
    since: datetime.datetime = None,
    max_action_age: int = None,
    max_minutes: int = None,
) -> None:
    if limit is None:
        limit = get_feature_int("voter_action_check", "max_recheck")
        if not limit:
            logger.info("voter_action_check disabled or max_recheck==0")
            return

    recheck_any(limit=limit, state=state, max_minutes=max_minutes)


@shared_task
def recheck_any(
    limit: int = None,
    state: str = None,
    min_check_interval: int = None,
    max_action_age: int = None,
    max_minutes: int = None,
) -> None:

    if max_minutes is None:
        max_minutes = get_feature_int(
            "voter_action_check", "max_recheck_any_minutes"
        ) or (settings.VOTER_CHECK_INTERVAL_MINUTES // 2)

    _recheck_old_actions(
        limit=limit,
        state=state,
        min_check_interval=min_check_interval,
        max_action_age=max_action_age,
        max_minutes=max_minutes,
    )


def _recheck_old_actions(
    limit: int = None,
    state: str = None,
    min_check_interval: int = None,
    since: datetime.datetime = None,
    max_action_age: int = None,
    max_minutes: int = None,
) -> int:
    # start with actions we've previously tried to match
    query = Action.objects.filter(last_voter_lookup__isnull=False)

    # unmatched or unregistered
    query = query.filter(Q(voter_id__isnull=True) | Q(voter__registered=False))

    if not since:
        # don't recheck things we recently checked
        if min_check_interval is None:
            min_check_interval = (
                get_feature_int("voter_action_check", "recheck_internal_days")
                or settings.VOTER_RECHECK_INTERVAL_DAYS
            )
        since = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(
            days=min_check_interval
        )
    query = query.filter(last_voter_lookup__lt=since)

    # ignore very old actions
    if max_action_age is None:
        max_action_age = (
            get_feature_int("voter_action_check", "recheck_max_days")
            or settings.VOTER_RECHECK_MAX_DAYS
        )
    action_cutoff = datetime.datetime.now(
        tz=datetime.timezone.utc
    ) - datetime.timedelta(days=max_action_age)
    query = query.filter(created_at__gt=action_cutoff)

    if state:
        query = query.filter(
            Q(lookup__state_id=state)
            | Q(registration__state_id=state)
            | Q(ballotrequest__state_id=state)
            | Q(reminderrequest__state_id=state)
        )
    else:
        # make sure it matches an item that we actually check
        query = query.filter(
            Q(lookup__isnull=False)
            | Q(registration__isnull=False)
            | Q(ballotrequest__isnull=False)
            | Q(reminderrequest__isnull=False)
        )

    if not max_minutes:
        max_minutes = settings.VOTER_CHECK_INTERVAL_MINUTES

    if limit and state == "WI":
        # adjust limit for queue rate
        limit = int(
            limit
            * settings.BULK_QUEUE_RATE_LIMITS["voter"]
            / settings.BULK_QUEUE_RATE_LIMITS["voter-wi"]
        )

    queue_async = get_feature_bool("voter_action_check", "recheck_async")
    if not queue_async:
        stop = datetime.datetime.utcnow() + datetime.timedelta(minutes=max_minutes)

    count = query.count()
    if not count:
        return 0

    logger.info(
        f"Recheck old actions limit {limit} of {count} in {state} since {since} "
        f"(min_check_interval {min_check_interval}, max_action_age {max_action_age}, "
        f"max_minutes {max_minutes})"
    )

    query = query.order_by("created_at")
    if limit:
        query = query[:limit]

    checked = 0
    for action in query:
        if queue_async:
            if state == "WI":
                voter_lookup_action.apply_async(
                    args=(str(action.uuid),),
                    expires=(max_minutes * 60),
                    queue=f"voter-wi",
                )
            else:
                voter_lookup_action.apply_async(
                    args=(str(action.uuid),), expires=(max_minutes * 60)
                )
            checked += 1
        else:
            item = action.get_source_item()
            if item:
                lookup(item)
                checked += 1
            if stop < datetime.datetime.utcnow():
                logger.info(f"Hit max runtime ({max_minutes} minutes)")
                break

    return checked


@shared_task(queue="voter")
def voter_lookup_action(pk):
    if not get_feature("voter_action_check"):
        logger.info("voter_action_check disabled")
        return
    action = Action.objects.get(uuid=pk)
    item = action.get_source_item()
    if item:
        lookup(item)
