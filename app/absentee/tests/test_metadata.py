import json
import os

import pytest
from jsonschema import validate

from common.pdf.pypdftk import PyPDFTK

from ..state_pdf_data import (
    STATE_DATA,
    each_block,
    each_block_of_type,
    each_slug,
    each_slug_with_type,
)
from .test_data import (
    STATE_ID_NUMBER_SLUGS,
    STATES_WITH_METADATA,
    get_filled_slugs,
    make_test_data,
)

schema_file = os.path.join(
    os.path.dirname(__file__), "../templates/pdf/states.schema.json"
)
with open(schema_file) as f:
    json_schema = json.load(f)


# Test that every YAML matches the schema
@pytest.mark.parametrize("state", STATES_WITH_METADATA)
def test_schema(state):
    state_data = STATE_DATA[state]
    validate(instance=state_data, schema=json_schema)


# Test various non-schema invariants
@pytest.mark.parametrize("state", STATES_WITH_METADATA)
def test_all_formats_have_error_message(state):
    state_data = STATE_DATA[state]
    for block in each_block_of_type(state_data, "text"):
        if block.get("format"):
            assert (
                block.get("format_error") is not None
            ), f"{block.get('slug')} has format but not format_error"

        if block.get("format_error"):
            assert (
                block.get("format") is not None
            ), f"{block.get('slug')} has format_error but not format"


@pytest.mark.parametrize("state", STATES_WITH_METADATA)
def test_boolean_valued_radios(state):
    state_data = STATE_DATA[state]
    for block in each_block_of_type(state_data, "radio"):
        # Just looking at boolean-valued radios
        if block.get("slug"):
            continue

        # Options should not have values (they can have slugs)
        for opt in block.get("options", []):
            assert (
                "value" not in opt
            ), f"Boolean-valued radio option with label {opt.get('label')} had a value. Use slugs for boolean radios."


@pytest.mark.parametrize("state", STATES_WITH_METADATA)
def test_string_valued_radios(state):
    state_data = STATE_DATA[state]
    for block in each_block_of_type(state_data, "radio"):
        # Just looking at string-valued radios
        if not block.get("slug"):
            continue

        # Options should not have slugs (they can have values)
        for opt in block.get("options", []):
            assert (
                "slug" not in opt
            ), f"String-valued radio option with label {opt.get('label')} had a slug. Use values for string radios."


@pytest.mark.parametrize("state", STATES_WITH_METADATA)
@pytest.mark.django_db
def test_copy_targets(state):
    state_data = STATE_DATA[state]

    # Valid targets for a "copy" are the fields from form_fields, as well
    # as all of the automatic fields we fill from the BallotRequest record
    _, record_filled_fields = make_test_data()

    slugs = [
        s
        for s in each_slug(
            state_data, include_auto_fields=False, include_manual_fields=False
        )
    ] + list(record_filled_fields.keys())

    for auto_field in state_data.get("auto_fields", []):
        # Only looking at copy fields
        if auto_field["type"] != "copy":
            continue

        assert (
            auto_field["field"] in slugs
        ), f"In auto_field {auto_field['slug']}, copy target {auto_field['field']} is not a valid field"


@pytest.mark.parametrize("state", STATES_WITH_METADATA)
@pytest.mark.django_db
def test_conditional_targets(state):
    state_data = STATE_DATA[state]

    # Valid targets for a "copy" are the fields from form_fields, as well
    # as all of the automatic fields we fill from the BallotRequest record
    _, record_filled_fields = make_test_data()

    slugs = [
        s
        for s in each_slug(
            state_data, include_auto_fields=False, include_manual_fields=False
        )
    ] + list(record_filled_fields.keys())

    for auto_field in state_data.get("auto_fields", []):
        # Only looking at copy fields
        if auto_field["type"] != "conditional":
            continue

        if not auto_field["fill"].get("value_from"):
            continue

        assert (
            auto_field["fill"]["value_from"] in slugs
        ), f"In auto_field {auto_field['fill']['slug']}, value_from target {auto_field['fill']['value_from']} is not a valid field"


# Make sure the fields in the YAML match the fields in the PDF
@pytest.mark.parametrize("state", STATES_WITH_METADATA)
@pytest.mark.django_db
def test_slugs_match_pdf(state):
    state_data = STATE_DATA[state]

    # The PDF can contain fields from the YAML, as well as all of the automatic
    # fields we fill from the BallotRequest record
    filled_slugs = get_filled_slugs()

    yaml_slugs = []
    boolean_slugs = ["us_citizen", "has_mailing_address", "same_mailing_address"]
    for slug, slug_type in each_slug_with_type(state_data):
        yaml_slugs.append(slug)

        if slug_type == "boolean":
            boolean_slugs.append(slug)

    valid_slugs = filled_slugs + yaml_slugs

    pdf_fields = PyPDFTK().dump_data_fields(
        os.path.join(os.path.dirname(__file__), f"../templates/pdf/states/{state}.pdf")
    )
    pdf_slugs = [f["FieldName"][0] for f in pdf_fields]

    # state_id_number_opt_* fields get filled in by state_id_number -- so if
    # a state_id_number_opt_* is in the PDF, state_id_number is effectively in
    # the PDF (it has to be present in the form fields)
    if any((slug in pdf_slugs) for slug in STATE_ID_NUMBER_SLUGS):
        pdf_slugs.append("state_id_number")

    # Ensure every field in the PDF matches up to either a slug from the YAML
    # or a slug that we auto-fill from the record
    missing_yaml_slugs = [slug for slug in pdf_slugs if slug not in valid_slugs]
    assert (
        len(missing_yaml_slugs) == 0
    ), f"Some slugs appear in the PDF but not the YAML: {missing_yaml_slugs}"

    # Ensure every slug in the YAML matches up to a field in the PDF
    missing_pdf_slugs = [slug for slug in yaml_slugs if slug not in pdf_slugs]
    assert (
        len(missing_pdf_slugs) == 0
    ), f"Some slugs appear in the YAML but not the PDF: {missing_pdf_slugs}"

    # Ensure every boolean slug points to a Button that uses On/Off as values
    for field in pdf_fields:
        if field["FieldName"][0] in boolean_slugs and (
            field["FieldName"][0] not in STATE_ID_NUMBER_SLUGS
        ):
            assert (
                field["FieldType"][0] == "Button"
            ), f"Expected PDF field {field['FieldName']} to be a checkbox"
            assert (
                "On" in field["FieldStateOption"]
            ), f"Expected PDF field {field['FieldName']} to use \"On\" as its checked value"


# Make sure page counts are correct
@pytest.mark.parametrize("state", STATES_WITH_METADATA)
def test_page_counts(state):
    state_data = STATE_DATA[state]

    page_count = PyPDFTK().get_num_pages(
        os.path.join(os.path.dirname(__file__), f"../templates/pdf/states/{state}.pdf")
    )

    assert state_data["pages"] == page_count
