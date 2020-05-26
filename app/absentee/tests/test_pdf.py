import json
import os
import random
import string

import pytest
from jsonschema import validate
from model_bakery import baker

from common.pdf.pypdftk import PyPDFTK

from ..generateform import ballot_request_is_emailable, process_ballot_request
from ..state_pdf_data import STATE_DATA, each_slug_with_type
from .test_data import (
    ALL_STATES,
    TEST_BALLOT_REQUEST_IS_18_OR_OVER,
    TEST_BALLOT_REQUEST_STATE_ID_NUMBER,
    make_test_data,
)


def random_string(length=8):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


# Test generating a PDF for each state
@pytest.mark.parametrize("state", ALL_STATES)
@pytest.mark.django_db
def test_gen_pdf(state, mocker):
    patched_leo_email = mocker.patch(
        "absentee.generateform.send_ballotrequest_leo_email"
    )
    patched_notification = mocker.patch(
        "absentee.generateform.send_ballotrequest_notification"
    )

    state_record = baker.make_recipe("election.state", code=state)
    ballot_request, expected_data = make_test_data(state_record)

    if STATE_DATA.get(state):
        state_data = STATE_DATA[state]

        # General sample data for all the state-specific field
        ballot_request.state_fields = {}

        for slug, slug_type in each_slug_with_type(
            state_data, include_auto_fields=False
        ):
            if slug == "us_citizen":
                expected_data[slug] = ballot_request.us_citizen
            elif slug == "is_18_or_over":
                expected_data[slug] = TEST_BALLOT_REQUEST_IS_18_OR_OVER
            elif slug == "state_id_number":
                expected_data[slug] = TEST_BALLOT_REQUEST_STATE_ID_NUMBER
            elif slug_type == "boolean":
                expected_data[slug] = True
                ballot_request.state_fields[slug] = True
            elif slug_type == "string":
                val = random_string()
                expected_data[slug] = val
                ballot_request.state_fields[slug] = val

    print(ballot_request.state_fields)

    # Generate the PDF!
    process_ballot_request(
        ballot_request,
        TEST_BALLOT_REQUEST_STATE_ID_NUMBER,
        TEST_BALLOT_REQUEST_IS_18_OR_OVER,
    )

    # Make sure the job to send the result was queued
    if ballot_request_is_emailable(ballot_request):
        patched_leo_email.delay.assert_called_once_with(ballot_request.uuid)
    else:
        patched_notification.delay.assert_called_once_with(ballot_request.uuid)

    # Dump the data from the generated PDF and make sure it matches up
    result_data = PyPDFTK().dump_data_fields(
        f"uploads/{ballot_request.result_item.file.name}"
    )

    print(result_data)

    for field in result_data:
        name = field["FieldName"][0]
        expected_value = expected_data.get(name)
        if expected_value:
            if expected_value == True:
                expected_value = "On"

            actual_value = field.get("FieldValue", [None])[0]
            assert (
                actual_value == expected_value
            ), f"Mismatch for field {name}: expected {expected_value}, got {actual_value}"
