# Election Information API

The Election Information API powers the VoteAmerica website and suite of tools.

It is available for others to use at no cost. If you build applications that integrate with it, please let us know so we can send you important data updates and new features.

This data has been gathered and vetted by our research staff, but if you see an error please [report it](https://www.voteamerica.com/report-incorrect-info/).

The API base URL is `https://api.voteamerica.com/v1/`. For example, you can try running `curl https://api.voteamerica.com/v1/election/field/`.

## GET `/election/field/`

Returns an array of state information field objects. Each contains a slug, a longer description, and a field format type.

Slugs can be matched to the results in `/state/{state}`. Descriptions are used as headers on VoteAmerica.com

### Field Types

You can find a listing of all of the 90+ Election Information API fields [on our website](https://www.voteamerica.com/election-data-api-fields/).

### 2020-Specific Data

For the 2020 General Election, we provide fields with specific dates in addition to our generic data, e.g. `received by October XX, 2020` vs. `received XX days before Election Day`. The correlation between generic fields and 2020 fields is as follows:

|Generic Field|2020 Field|
| ---- | ---- |
|`early_voting_ends`|`2020_early_voting_ends`|
|`early_voting_starts`|`2020_early_voting_starts`|
|`registration_deadline_in_person`|`2020_registration_deadline_in_person`|
|`registration_deadline_mail`|`2020_registration_deadline_by_mail`|
|`registration_deadline_online`|`2020_registration_deadline_online`|
|`vbm_deadline_in_person`|`2020_vbm_request_deadline_by_in_person`|
|`vbm_deadline_mail`|`2020_vbm_request_deadline_by_mail`|
|`vbm_deadline_online`|`2020_vbm_request_deadline_online`|
|`vbm_voted_ballot_deadline_in_person`|`2020_ballot_return_deadline_in_person`|
|`vbm_voted_ballot_deadline_mail`|`2020_ballot_return_deadline_by_mail`|

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


