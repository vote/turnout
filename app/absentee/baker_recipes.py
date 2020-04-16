from django_smalluuid.models import uuid_default
from model_bakery.recipe import Recipe, foreign_key

from common import enums
from election.models import State
from official.models import Region

from .models import BallotRequest

ballot_request_state = Recipe(State, code="XX")
ballot_request_mailing_state = Recipe(State, code="YY")
ballot_request_region = Recipe(Region, external_id=431101)  # Cambridge, MA

ballot_request = Recipe(
    BallotRequest,
    state=foreign_key(ballot_request_state),
    mailing_state=foreign_key(ballot_request_mailing_state),
    result_item=None,
    status=enums.TurnoutActionStatus.PENDING,
    phone="+1617555123",
    us_citizen=True,
    sms_opt_in=True,
    region=foreign_key(ballot_request_region),
    uuid=uuid_default(),
    _fill_optional=True,
)
