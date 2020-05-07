from django_smalluuid.models import uuid_default
from model_bakery.recipe import Recipe, foreign_key

from common import enums
from election.models import State
from official.baker_recipes import region

from .models import BallotRequest

state = Recipe(State, code="XX")
mailing_state = Recipe(State, code="YY")

ballot_request = Recipe(
    BallotRequest,
    state=foreign_key(state),
    mailing_state=foreign_key(mailing_state),
    result_item=None,
    status=enums.TurnoutActionStatus.PENDING,
    phone="+1617555123",
    us_citizen=True,
    sms_opt_in=True,
    region=foreign_key(region),
    uuid=uuid_default(),
    _fill_optional=True,
)

STATE_ID_NUMBER = "123-45-6789"
IS_18_OR_OVER = True
