import os
import uuid
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from model_bakery.recipe import Recipe, foreign_key

from common import enums
from election.models import State
from official.baker_recipes import region
from storage.models import SecureUploadItem

from .models import BallotRequest, LeoContactOverride


def open_signature_file():
    with open(
        os.path.join(os.path.dirname(__file__), "tests/fixtures/sig.jpeg"), "rb",
    ) as f:
        data = BytesIO(f.read())

    return SimpleUploadedFile("sig.jpg", data.getvalue())


state = Recipe(State, code="XX", allow_print_and_forward=True)
mailing_state = Recipe(State, code="YY")
request_mailing_state = Recipe(State, code="ZZ")
signature = Recipe(
    SecureUploadItem,
    upload_type="Signature",
    content_type="image/jpeg",
    file=open_signature_file(),
)

ballot_request = Recipe(
    BallotRequest,
    state=foreign_key(state),
    mailing_state=foreign_key(mailing_state),
    request_mailing_state=foreign_key(request_mailing_state),
    result_item=None,
    result_item_mail=None,
    status=enums.TurnoutActionStatus.PENDING,
    phone="+1617555123",
    us_citizen=True,
    sms_opt_in=True,
    region=foreign_key(region),
    uuid=uuid.uuid4,
    signature=foreign_key(signature),
    esign_method=enums.SubmissionType.SELF_PRINT,
    search=None,
    _fill_optional=True,
)

STATE_ID_NUMBER = "123-45-6789"
IS_18_OR_OVER = True

leo_contact_override = Recipe(
    LeoContactOverride, region=foreign_key(region), _fill_optional=True
)
