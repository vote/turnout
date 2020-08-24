# State Voter Tool Uptime API

VoteAmerica monitors state voter tool web sites.  The uptime API
allows you to query the current and historical uptime of these sites.

We monitor all sites that are referenced by ``external_tool_*`` fields
in the [election information data](index.md) API.

The API base url is `https://api.voteamerica.com/v1/`. For example, you can try running `curl https://api.voteamerica.com/v1/election/field/`.

## GET `/leouptime/sites/`

List per-State voter tools that we monitor, along with their uptime stats.

Example response:

```json
{
  "count": 196,
  "next": "https://api.voteamerica.com/v1/leouptime/sites/?limit=100&offset=100",
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
  "next": "https://api.voteamerica.com/v1/leouptime/sites/?limit=100&offset=100",
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
