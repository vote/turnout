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


## GET `/leouptime/sites/`

List per-State voter tools that we monitor, along with their uptime stats.

Example response:

```json
{
  "count": 196,
  "next": "http://vapre.us.to:19001/v1/leouptime/sites/?limit=100&offset=100",
  "previous": null,
  "results": [
    {
      "uuid": "3ad3c7a1-477a-4e51-955b-b7bdffbf1597",
      "url": "https://myvoteinfo.voteks.org/VoterView/AbsenteeBallotSearch.do",
      "description": "KS Absentee Ballot Tracker",
      "state_up": true,
      "state_changed_at": "2020-07-24T16:22:42.394383Z",
      "last_went_down_check": null,
      "last_went_up_check": null,
      "last_tweet_at": null,
      "uptime_day": 1,
      "uptime_week": 1,
      "uptime_month": 1,
      "uptime_quarter": 1
    },
    ...
  ]
}
```

## GET `/leouptime/sites-down/`

List sites that currently appear to be down.

Example response:

```json
{
  "count": 196,
  "next": "http://vapre.us.to:19001/v1/leouptime/sites/?limit=100&offset=100",
  "previous": null,
  "results": [
    {
      "uuid": "3ad3c7a1-477a-4e51-955b-b7bdffbf1597",
      "url": "https://myvoteinfo.voteks.org/VoterView/AbsenteeBallotSearch.do",
      "description": "KS Absentee Ballot Tracker",
      "state_up": false,
      "state_changed_at": "2020-07-24T16:22:42.394383Z",
      "last_went_down_check": {
        "uuid": "b8e40efa-125b-4eb9-bd36-90de6418fdc7",
        "site": "3ad3c7a1-477a-4e51-955b-b7bdffbf1597",
        "state_up": false,
        "ignore": false,
        "load_time": 1.398545,
        "error": "faking CA downtime",
        "proxy": "11b895af-004b-4b7c-9ce0-c3a7d842013d",
        "created_at": "2020-07-24T16:31:46.560065Z"
      },
      "last_went_up_check": null,
      "last_tweet_at": null,
      "uptime_day": 1,
      "uptime_week": 1,
      "uptime_month": 1,
      "uptime_quarter": 1
    },
    ...
  ]
}
```

## GET `/leouptime/sites/<uuid>/`

Get site detail

Example response:

```json
{
  "uuid": "11b895af-004b-4b7c-9ce0-c3a7d842013d",
  "url": "https://california.ballottrax.net/voter/",
  "description": "CA Absentee Ballot Tracker",
  "state_up": true,
  "state_changed_at": "2020-07-24T16:48:29.429225Z",
  "last_went_down_check": {
    "uuid": "662326f6-31dd-42e7-bce6-49e2f4ee3b38",
    "site": "11b895af-004b-4b7c-9ce0-c3a7d842013d",
    "state_up": false,
    "ignore": false,
    "load_time": 1.398545,
    "error": "faking CA downtime",
    "proxy": "11b895af-004b-4b7c-9ce0-c3a7d842013d",
    "created_at": "2020-07-24T16:31:46.560065Z"
  },
  "last_went_up_check": {
    "uuid": "96469a47-4276-4f79-a3f9-df2dc8ea2607",
    "site": "11b895af-004b-4b7c-9ce0-c3a7d842013d",
    "state_up": true,
    "ignore": false,
    "load_time": 1.578655,
    "error": null,
    "proxy": "11b895af-004b-4b7c-9ce0-c3a7d842013d",
    "created_at": "2020-07-24T16:48:29.429225Z"
  },
  "last_tweet_at": null,
  "uptime_day": 0.988392718056286,
  "uptime_week": 0.998341816865184,
  "uptime_month": 0.999613090601876,
  "uptime_quarter": 0.999871030200625
}
```

## GET `/leouptime/sites/<uuid>/checks/`

List all past checks for a site, along with latency and error result (if any).

Example response:

```json
{
  "count": 14,
  "next": null,
  "previous": null,
  "results": [
    {
      "uuid": "804f301c-e213-495b-ae3f-27eb05d45511",
      "site": "96469a47-4276-4f79-a3f9-df2dc8ea2607",
      "state_up": true,
      "ignore": false,
      "load_time": 1.252124,
      "error": null,
      "proxy": "f5fca2f0-8d38-49af-871f-7bc2e35cb720",
      "created_at": "2020-07-24T18:18:35.203120Z"
    },
    ...
  ]
}
```

## GET `/leouptime/sites/<uuid>/downtime/`

List all intervals of observed downtime for a site.

Example response:
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "uuid": "2bac112c-2130-40b5-8ec0-7f73ece24415",
      "site": "46443124-6c99-498f-be79-6c14db918616",
      "down_check": {
        "uuid": "fd460992-67c1-47a3-99f6-b731317c7c84",
        "site": "46443124-6c99-498f-be79-6c14db918616",
        "state_up": false,
        "ignore": false,
        "load_time": 1.398545,
        "error": "faking CA downtime",
        "proxy": "341c5c1f-4f03-4a9e-a13c-42bcffb44ff2",
        "created_at": "2020-07-24T16:31:46.560065Z"
      },
      "up_check": {
        "uuid": "a786d864-4a5f-474c-933b-7cebbf0584a2",
        "site": "46443124-6c99-498f-be79-6c14db918616",
        "state_up": true,
        "ignore": false,
        "load_time": 1.578655,
        "error": null,
        "proxy": "341c5c1f-4f03-4a9e-a13c-42bcffb44ff2",
        "created_at": "2020-07-24T16:48:29.429225Z"
      }
    },
    ...
  ]
}
```

## GET `/leouptime/downtime/`

List all downtime intervals for all sites.

Example response:
```json
{
  "count": 4,
  "next": null,
  "previous": null,
  "results": [
    {
      "uuid": "3d36c940-7373-46a3-9bef-4e23c785dd4c",
      "site": "36ba4be8-8f8f-4eaf-832e-d2e3a06de534",
      "down_check": {
        "uuid": "f6628db1-b7e9-468a-85b6-5d5265e46f96",
        "site": "36ba4be8-8f8f-4eaf-832e-d2e3a06de534",
        "state_up": false,
        "ignore": false,
        "load_time": 1.636585,
        "error": "faking CA downtime",
        "proxy": "1346fc6a-0559-41f3-82f6-e3633356c608",
        "created_at": "2020-07-24T16:34:33.698758Z"
      },
      "up_check": {
        "uuid": "412c7529-7238-4c0a-924b-884ba8123adb",
        "site": "36ba4be8-8f8f-4eaf-832e-d2e3a06de534",
        "state_up": true,
        "ignore": false,
        "load_time": 2.080274,
        "error": null,
        "proxy": "1346fc6a-0559-41f3-82f6-e3633356c608",
        "created_at": "2020-07-24T16:46:58.231752Z"
      }
    },
    ...
  ]
}
```
