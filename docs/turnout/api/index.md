# Election Information API

The Election Information API powers the VoteAmerica website and suite of tools.

It is available for others to use at no cost. If you build applications that integrate with it, please let us know so we can send you important data updates and new features.

This data has been gathered and vetted by our research staff, but if you see an error please [report it](https://www.voteamerica.com/report-incorrect-info/).

The API base URL is `https://api.voteamerica.com/v1/`. For example, you can try running `curl https://api.voteamerica.com/v1/election/field/`.

## GET `/election/field/`

Returns an array of state information field objects. Each contains a slug, a longer description, and a field format type.

Slugs can be matched to the results in `/state/{state}`. Descriptions are used as headers on VoteAmerica.com

### Field Types

|slug|description|field format|
| ---- | ---- | ---- |
|`2020_general_election_date`|2020 general election date|Date|
|`2020_official_election_calendar`|2020 election calendar|URL|
|`alert_registration`|Registration alert|Text|
|`alert_vbm`|Absentee alert|Text|
|`early_voting_ends`|Early voting ends|Text|
|`early_voting_notes`|Early voting notes|Text|
|`early_voting_starts`|Early voting starts|Text|
|`election_protection_phone`|state-specific election protection hotline number|Phone|
|`election_protection_website`|State-specific election protection website|URL|
|`external_tool_absentee_ballot_tracker`|The tool used to track your VBM ballot|URL|
|`external_tool_ovr`|Official tool OVR|URL|
|`external_tool_polling_place`|Official polling place locator|URL|
|`external_tool_vbm_application`|Official tool vote by mail application|URL|
|`external_tool_verify_status`|Official tool verify status|URL|
|`id_requirements_in_person_registration`|ID requirements in person registration|Markdown|
|`id_requirements_in_person_voting`|ID requirements for voting in-person|Markdown|
|`id_requirements_ovr`|ID requirements online registration|Markdown|
|`id_requirements_sdr`|ID requirements same day registration|Markdown|
|`id_requirements_vbm`|ID requirements for VBM|Markdown|
|`leo_absentee_ballots`|Local Election Office - Absentee Ballots|URL|
|`leo_overseas_voters`|Local Election Office - Overseas Voters|URL|
|`leo_voter_registration`|Local Election Office - voter registration|URL|
|`official_info_early_voting`|The state's page for early voting information|URL|
|`official_info_felon`|The state's page for felon re-enfranchisement info|URL|
|`official_info_registration`|The state's page for voter registration info|URL|
|`official_info_students`|The state's page for registering to vote as a student|URL|
|`official_info_vbm`|The state's page for VBM info|URL|
|`official_info_voter_id`|The state's page for voter ID info|URL|
|`overseas_fvap_directions`|State-specific FVAP page for directions|URL|
|`overseas_fvap_tool`|State-specific page at fvap.gov|URL|
|`pdf_absentee_form`|PDF for the VBM application|URL|
|`polls_close`|Polls close|Text|
|`polls_open`|Polls open|Text|
|`registration_automatic_exists`|Voters are registered automatically|Boolean|
|`registration_deadline_in_person`|Voter registration deadline (in-person)|Text|
|`registration_deadline_mail`|Voter registration deadline (by-mail)|Text|
|`registration_deadline_online`|Voter registration deadline (online)|Text|
|`registration_directions`|Voter registration directions|Markdown|
|`registration_minimum_age`|Voter registration minimum age|Text|
|`registration_notes`|Voter registration notes|Markdown|
|`registration_nvrf_box_6`|National Voter Registration Form Box 6 - ID number|Markdown|
|`registration_nvrf_box_7`|National Voter Registration Form Box 7 - Choice of Party|Markdown|
|`registration_nvrf_box_8`|National Voter Registration Form Box 8 - Race or ethnic group|Markdown|
|`registration_nvrf_submission_address`| NVRF submission address. This is also the address of the state-wide election office.|Text|
|`registration_rules`|Voter registration rules|Markdown|
|`registration_submission_email`|Registration - can you submit your form via email?|Boolean|
|`registration_submission_fax`|Registration - can you fax your voter reg form?|Boolean|
|`registration_submission_in_person`|Registration - can you register to vote in person?|Boolean|
|`registration_submission_mail`|Registration - can you submit your form via mail?|Boolean|
|`registration_submission_phone`|Registration - can you register to vote via phone?|Boolean|
|`sdr_early_voting`|Allows same day registration during the early voting period|Boolean|
|`sdr_election_day`|Allows Election Day registration?|Boolean|
|`sdr_notes`|Same Day Registration (notes)|Text|
|`sdr_where`|Same day registration locations|Text|
|`sos_contact_email`|Statewide election email. Generally the SOS|Email|
|`sos_election_website`|Statewide election website. Generally the SOS|URL|
|`sos_phone_number`|Statewide election phone number. Generally the SOS|Phone|
|`vbm_absentee_ballot_rules`|VBM rules|Markdown|
|`vbm_application_directions`|VBM application directions|Markdown|
|`vbm_app_submission_email`|VBM - can you submit your app via email?|Boolean|
|`vbm_app_submission_fax`|VBM - can you submit your app via fax?|Boolean|
|`vbm_app_submission_in_person`|VBM - can you submit your app in person?|Boolean|
|`vbm_app_submission_mail`|VBM - can you submit your app via mail?|Boolean|
|`vbm_app_submission_phone`|VBM - can you apply via phone?|Boolean|
|`vbm_deadline_in_person`|VBM signup deadline (in-person)|Text|
|`vbm_deadline_mail`|VBM signup deadline (by-mail)|Text|
|`vbm_deadline_online`|VBM signup deadline (online)|Text|
|`vbm_first_day_to_apply`|VBM earliest day to apply|Text|
|`vbm_no_excuse`|Allows no excuse VBM?|Boolean|
|`vbm_notes`|VBM notes|Text|
|`vbm_permanent_anyone`|Allows any citizen to opt-in for permanent VBM?|Boolean|
|`vbm_permanent_disabled`|Disabled / Elderly / Sick Permanent VBM Possible?|Boolean|
|`vbm_state_provides_ballot_postage`|Does the state provide postage for the ballot so that the citizen doesn't need own stamp?|Boolean|
|`vbm_state_provides_dropboxes`|VBM State Provides Ballot Dropboxes|Boolean|
|`vbm_voted_ballot_deadline_in_person`|VBM voted ballot deadline to return in person|Text|
|`vbm_voted_ballot_deadline_mail`|VBM voted ballot deadline. Indicates postmarked or received.|Text|

## GET `/election/state/{state}/`

Returns all elections information fields for a single state. `{state}` should be a 2-letter postal abbreviation, in upper case.

```json
{
    "code": string,
    "name": string,
    "state_information": [
        {
            "text": string,
            "field_type": string,
            "modified_at": datetime
        }
    ]
}
```

## GET `/official/address/`

Map an address to a Voting Region. A Voting Region is a geographic area that is served by a particular election office.

You must provide the following URL parameters to this endpoint:

- `address1`: First line of the street address
- `city`: Name of the city
- `state`: Two-letter state code
- `zipcode`: Five-digit ZIP code

For example, `https://api.voteamerica.com/v1/official/address/?address1=1600+Pennsylvania+Ave&city=Washington&state=DC&zipcode=20006`

The endpoint will return a list of possible regions. In almost all cases, the list will have just a single region, but there are some ambiguous addresses where we may return multiple possible regions. We may also return no regions if we were not able to determine the region for the address. If that provided address could not be geocoded (typically because the address is invalid), this endpoint will return a `400` status code.

Example response:

```json
[
    {
        "name": "District of Columbia",
        "external_id": 430653
    }
]
```

The `external_id` can be used to link to the VoteAmerica LEO contact page for that region, e.g. `https://www.voteamerica.com/local-election-offices/DC/430653/`. It can also be used to match to a region in the [US Vote Foundation Data Set](https://civicdata.usvotefoundation.org/content/local-election-official-and-office-contact-data){target=_blank}. You'll need to [reach out to the US Vote Foundation](https://civicdata.usvotefoundation.org/#request-access){target=_blank} for access to that data set.


