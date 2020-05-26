import glob
import os

import yaml

STATE_DATA = {}

for fname in glob.glob("absentee/templates/pdf/states/*.yml"):
    state, _ = os.path.splitext(os.path.basename(fname))
    with open(fname) as f:
        STATE_DATA[state.upper()] = yaml.safe_load(f)

# Helpers for traversing state_data


def each_block(state_data):
    """
    Yield each form input block, including nested conditionals.
    """
    for section in state_data.get("form_fields", []):
        for block in section.get("content", []):
            yield block

            for subblock in block.get("conditional", []):
                yield subblock

            for option in block.get("options", []):
                for subblock in option.get("conditional", []):
                    yield subblock


def each_block_of_type(state_data, type_name):
    """
    Like each_block, but filtered to a specific type
    """
    for block in each_block(state_data):
        if block["type"] == type_name:
            yield block


def each_slug_with_type(
    state_data,
    include_input_blocks=True,
    include_auto_fields=True,
    include_manual_fields=True,
):
    """
    Yields each slug that's referenced in this state data. This includes:
    - slugs from form input blocks
    - slugs filled by auto_fields
    - slugs listed in manual_fields
    """
    if include_input_blocks:
        for block in each_block(state_data):
            if block.get("slug"):
                if block["type"] == "checkbox":
                    yield (block["slug"], "boolean")
                else:
                    yield (block["slug"], "string")

            for option in block.get("options", []):
                if option.get("slug"):
                    yield (option["slug"], "boolean")

    if include_auto_fields:
        for auto_field in state_data.get("auto_fields", []):
            yield (auto_field["slug"], "string")

    if include_manual_fields:
        for slug in state_data.get("manual_fields", []):
            yield (slug, "unknown")


def each_slug(
    state_data,
    include_input_blocks=True,
    include_auto_fields=True,
    include_manual_fields=True,
):
    for slug, slug_type in each_slug_with_type(
        state_data, include_input_blocks, include_auto_fields, include_manual_fields
    ):
        yield slug
