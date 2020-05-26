# State Metadata

This documentation covers the format for the per-state YAML files. It is a companion to state_metadata.schema.json, which is a JSON Schema with the full definition of the format.

To get auto-complete and as-you-type validation in VS Code, you can install the [YAML](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml) plugin, and then add this config to `.vscode/settings.json` in this repo:

```json
{
  "yaml.schemas": {
      "app/absentee/templates/pdf/states.schema.json": "app/absentee/templates/pdf/states/*.yml",
  }
}
```

# `signatures`

The locations of any signatures fields on the document. A mapping of page number to location (`x`/`y`/`width`/`height`). The frontend doesn't need to worry about this field.

# `signature_statement`

This is a statement that appears on the form, and says what the user is signing. It should be shown in the front-end alongside the E-Sign UI. It may be `null`.

# `auto_fields`

State-specific fields that we can fill in automatically. The front-end does NOT need to know about these or fill them in; it's handled automatically on the backend.

This is an array of `slug` and `type`. The valid types are:

- `todays_date`: The current date, formatted as `MM/DD/YYYY`
- `static`: A static value, specified by the `value` key.
- `copy`: A copy of another field from the `state_fields` subfield, specified by the `field` key.

# `manual_fields`

This is a list of fields that are *not* filled in by Turnout (either automatically by `auto_fields`, or via user input by `form_fields`). This should be a full listing of every field in the PDF that's not otherwise referenced in the metadata file. Turnout doesn't use this, but the tests do -- in order to verify that a field isn't missing from `form_fields`, we need to know the list of field we *don't* expect to be filled by Turnout.

# `form_fields`

The state-specific fields on the form. This is loaded by the frontend, rendered as a form, and passed in the `state_fields` field of the API.

`form_fields` is an array of section. Each section has an array of blocks. Each block MUST have a `type`. Any block MAY have a `label` and a `note`. Any block MAY specify `required: true`. Other fields are type-dependent.

## Universal Form Fields

In addition to the fields listen in the metadata, the frontend must also ask the user for their region, and whether their mailing address is different from their registered address (and if so, what their mailing address is). This information should be passed in the following top-level API fields:

- `region`
- `mailing_address1`
- `mailing_address2`
- `mailing_city`
- `mailing_state`
- `mailing_zipcode`

## Slugs

Slugs are the names of the fields as they're represented in the API. They are passed either in the top-level of the API request, or nested in the `state_fields` subfield.

### Top-Level Form Fields

Some fields must be passed in as top-level API fields rather than in the `state_fields` API field. They are PII and are handled separately on the backend. These fields are:

- `us_citizen`
- `is_18_or_over`
- `state_id_number`

These fields are *not* required by every state, so they shouldn't be rendered by the frontend by default. They *may* appear as the `slug` for any field in the state-specific fields as described below.

### `state_fields` Fields

The rest of the form fields, as described by the `form_fields` block, should be passed by the frontend in the `state_fields` API field.

## Form Field Types

The types are as follows:

### `section`

A visual section of the form. `label` and `note` are optional. `content` must be an array of blocks to render inside this section. THe top level of `form_fields` are all `section`s, and `section`s cannot appear elsewhere (they can't be nested or used inside `conditional`s)

### `radio`

A set of radio buttons. By default, these should be rendered as a vertical list. If `layout: horizontal` is specified, they MAY be layed out horizontally if space permits (e.g. on desktop but not on mobile).

The `radio` block will have an array of `options`. Each option MUST have a `label`. Each option MAY have a `conditional`, which is an array of block to render if that option is selected. One option MAY have a `default: true`, in which case it should start out selected.

Unless the radio is marked as `required: true`, the frontend should offer a way to select no option, or deselect an option (for example, adding a "None" option).

There are two types of radios: *boolean-valued* and *string-valued*. A boolean-valued radio will *not* have a slug, but its options *may* have slugs. A string-valued radio
*will* have a slug, and its options *may* have `value` fields.

#### Radio Data Representation

For a *boolean-valued* radio, the frontend should pass the selected slug in `state_fields` with a value of `true`.

For example, in this block:

```yaml
- type: radio
  layout: horizontal
  options:
    - label: Democratic
      slug: party_democratic
    - label: Republican
      slug: party_republican
    - label: Non-Partisan
```

If the user picks "Democratic", the client should pass:

```json
"state_fields": {
    "party_democratic": true
}
```

But if the user picks "Non-Partisan", the client should not pass anything.

For a *string-valued* radio, the client should use the radio's slug as the key and the selected option's value as the value. For example, in this block:

```yaml
- type: radio
  slug: party
  layout: horizontal
  options:
    - label: Democratic
      value: Democratic
    - label: Republican
      value: Republican
    - label: Non-Partisan
```

If the user picks "Democratic", the client should pass:

```json
{
  "state_fields": {
      "party": "Democratic"
  }
}
```

But if the user picks "Non-Partisan", the client should not pass anything.

### `text`

A single-line text input. If `required: true` is set, the user must enter a non-empty string.

There MAY be `format` and `format_error` properties (if one is present, the other one will be as well). These specify a regular expression that should be used to validate the text input, and an error message that should be shown if the regular expression does not match (typically this will be a human-readable description of the regular expression). This regular expression will be compatible with the Javascript, RE2, and Python regular expression engines.

For example:

```yaml
- type: text
  label: Last 4 digits of your Social Security Number
  format: "\d{4}"
  format_error: "Enter 4 numeric digits"
```

#### Text Data Representation

The frontend should send the entered value. For example, in this block:


```yaml
- type: text
  label: Name of person delivering the ballot
  slug: ballot_hand_deliver_name
```

If the user enters "foo", the client should pass:

```json
{
  "state_fields": {
    "ballot_hand_deliver_name": "foo"
  }
}
```

Remember that if the `slug` is `state_id_number`, then the data MUST be passed in the top-level `state_id_number` field, and NOT in the `state_fields` subfield.

### `checkbox`

A single checkbox for the user to check. If `required: true` is set, this box MUST be checked for the user to submit the form. `label` is required.

There MAY be a `conditional` field, which will be an array of blocks to render if the checkbox is checked.

#### Checkbox Data Representation

If the checkbox has a slug, and it is checked, pass the slug as the key and `true` as the value.

```yaml
- type: checkbox
  label: I want to vote absentee in all elections.
  slug: all_elections
```

If the user checks the box, send:

```json
{
  "state_fields": {
      "all_elections": true
  }
}
```

If the user does not check the box, or there is no `slug`, the client should not pass anything.

Remember that if `slug` is `us_citizen` or `is_18_or_over`, you MUST pass this in the top-level API fields rather than in `state_fields`.

### `election_date`

The date of the election. It's up to the frontend how to fill this in: it could auto-fill with the
next upcoming election, or render a dropdown of options, or just a text box.

If this is the only block in a section, and the UI chooses not to render it (because it's being autofilled with the date of the next election, for example), the UI may choose to not render the whole section.

### Election Date Data Representation

`election_date` fields work just like `text` fields. The date must be formatted as `MM/DD/YYYY`.
