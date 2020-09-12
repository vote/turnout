import datetime
import logging
import uuid

from django.contrib.postgres.fields import JSONField
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from common.utils.models import TimestampModel, UUIDModel

logger = logging.getLogger("voter")


class Voter(UUIDModel, TimestampModel):
    """
    A Voter is an entry in the voter rolls.  It is not the _person_
    (who may move, or be registered twice), but rather an active
    registration of that person in a particular location.
    """

    state = models.ForeignKey("election.State", on_delete=models.PROTECT, null=True,)

    state_voter_id = models.TextField(null=True, db_index=True)
    state_result = JSONField(null=True)
    last_state_refresh = models.DateField(null=True)
    alloy_person_id = models.IntegerField(null=True, db_index=True)
    alloy_result = JSONField(null=True)
    last_alloy_refresh = models.DateTimeField(null=True)
    ts_voterbase_id = models.TextField(null=True, db_index=True)
    last_ts_refresh = models.DateTimeField(null=True)
    ts_result = JSONField(null=True)

    # registration status
    registered = models.BooleanField(null=True)
    registration_date = models.DateField(null=True)
    last_registration_refresh = models.DateTimeField(null=True)

    # deprecated:
    phone_id = models.UUIDField(null=True, editable=False, default=uuid.uuid4)

    # our contact info
    phone = PhoneNumberField(null=True)
    email = models.EmailField(max_length=150, null=True)

    # PII (pulled from or validated against a data source)
    first_name = models.TextField(null=True)
    middle_name = models.TextField(null=True)
    last_name = models.TextField(null=True)
    suffix = models.TextField(null=True)
    date_of_birth = models.DateField(null=True)

    address_full = models.TextField(null=True)
    city = models.TextField(null=True)
    zipcode = models.TextField(null=True)

    class Meta:
        ordering = ["-created_at"]

    def refresh_registration_status(
        self,
        registered: bool,
        register_date: datetime.datetime,
        last_updated: datetime.datetime,
    ):
        # convert old reg date to datetime for each comparisons
        if self.registration_date:
            old_reg_datetime = datetime.datetime(
                self.registration_date.year,
                self.registration_date.month,
                self.registration_date.day,
                tzinfo=datetime.timezone.utc,
            )
        else:
            old_reg_datetime = None
        if register_date and last_updated:
            assert register_date <= last_updated
        if registered:
            if (
                not self.last_registration_refresh
                or last_updated > self.last_registration_refresh
            ):
                if not old_reg_datetime or register_date > old_reg_datetime:
                    # a newer instance of registration
                    self.registration_date = register_date.date()
                self.registered = True
                self.last_registration_refresh = last_updated or register_date
        else:
            if (
                self.registered
                and last_updated
                and old_reg_datetime
                and self.last_registration_refresh
                and self.last_registration_refresh > old_reg_datetime
                and last_updated > self.last_registration_refresh
            ):
                # definitely unregistered
                self.registered = False
                self.registration_date = None
                self.last_registration_refresh = last_updated
            elif (
                not self.registered
                and self.last_registration_refresh
                and last_updated > self.last_registration_refresh
            ):
                # still not registered
                self.last_registration_refresh = last_updated


class TSEarlyVoteAndBallot(models.Model):
    smartvan_id = models.CharField(max_length=100, null=True)
    voterbase_id = models.CharField(max_length=100, primary_key=True)
    voterid = models.CharField(max_length=100, null=True)
    state = models.CharField(max_length=2, null=True, db_index=True)
    county = models.CharField(max_length=100, null=True)
    county_id = models.CharField(max_length=100, null=True)

    request_received_date = models.DateField(null=True)
    ballot_mailed_date = models.DateField(null=True)
    ballot_received_date = models.DateField(null=True)
    early_voted_date = models.DateField(null=True)
    ballot_party = models.CharField(max_length=100, null=True)
    ballot_canceled = models.DateField(null=True)
    application_mailed = models.DateField(null=True)

    tsmart_requested = models.CharField(max_length=100, null=True)
    tsmart_voted = models.CharField(max_length=100, null=True)

    election_date = models.DateField(null=True)
    ev_data_update_date = models.DateField(null=True)

    class Meta:
        db_table = "ts_early_vote_and_ballot"
