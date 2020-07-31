# VoteAmerica Action API
​
This API allows third-party partners to complete part of the voter registration
flow via API.

**This API is not available publicly. It is available to select partners who
work closely with us to make sure their usage of the API is compliant**. If
you're interested in this sort of integration, email
[partner@voteamerica.com](mailto:partner@voteamerica.com).

## Overview
​
The general flow is:

1. The partner sends a `POST` to `/v1/registration/external/request` with the
   basic info on the user.

2. VoteAmerica returns some text to show to the user (this will typically
   contain voter ID requirements, and any specific instructions on how to
   navigate the state online voter registration system), as well as between
   zero and two options for the user to pick from. These options may include
   going to the state's official voter registration website, or going to
   VoteAmerica to print and mail a paper form.

3. When a user clicks on a button that takes them to a state voter registration
   website, you MUST follow up with a `POST` to `/v1/event/track` to let
   VoteAmerica know that the user followed that link.
​
## Important Notes
​
Contact information sent to VoteAmerica will be used for our GOTV and ballot
chase programs. You must have permission from the user to share their
information with VoteAmerica. Submitting the `POST ` to
`/registration/external/request` opts the user into receiving text messages from
VoteAmerica, so you must show the following language (or substantially similar
language, approved by VoteAmerica) to the user:

```text
Powered by VoteAmerica. By hitting continue, you agree to VoteAmerica’s
[Terms](https://www.voteamerica.com/terms/sms/) and
[Privacy](https://www.voteamerica.com/privacy/). You will receive occasional
emails from VoteAmerica. You can unsubscribe at any time. If you provide your
cell phone number, you agree to receive occasional text messages from
VoteAmerica. Message and data rates may apply. Message frequency varies. Text
STOP to cancel and HELP for more info.
```
​
## API Endpoints
​
There are two endpoints in the Action API. For the purposes of this
documentation, we are using TypeScript notation for the data types. In
particular, a `?` after an object key indicates that that field is optional.
Otherwise, the field is required.

As part of the partnership setup process with VoteAmerica, we will give you
the base URL to send requests to. DO NOT send your requests to
`api.voteamerica.com`: that URL is behind CloudFlare and has rate-limiting
restrictions. We will set up a URL for you to hit with IP whitelisting that
can bypass the rate-limiting. All requests MUST be sent over HTTPS.

You will need to create an API key. You can do this from the VoteAmerica
admin tools.


### `POST /v1/registration/external/request/`

Auth: basic auth, API key ID as the username and API key secret as the password

Body: the fields from the first page of register:

```typescript
{
  // Optional, except in TN where it is required and "Mx" cannot
  // be used.
  title?: 'Mr' | 'Mrs' | 'Miss' | 'Ms' | 'Mx',

  first_name: string,
  middle_name?: string,
  last_name: string,
  suffix?: string,

  // ISO 8601, e.g. "2020-07-22"
  date_of_birth: string,

  // Must be a valid email
  email: string,

  // E.164 format, e.g. +16175551234
  phone?: string,

  address1: string,
  address2?: string,
  city: string,

  // Two-character state code, e.g. "MA". 50 states + "DC" are supported.
  state: string,

  // Five-character ZIP code
  zipcode: string,

  // Must be set to true to acknowledge that the user will be
  // opted in to VoteAmerica's shortcode program
  sms_opt_in: true,

  // Maybe be set to indicate that the user has opted in to your SMS
    // program (will be reflected in your subscriber data exports)
  sms_opt_in_subscriber?: true,
}
```

All strings that do not have specific validation requirements have a maximum
ength of 256 UTF-8 characters.

200 Response format:

```typescript
{
  message_markdown: string,
  buttons: Array<
    {
      message_text: string,

      // Exactly one button with have this property set to "true"
      primary: boolean,

      // The URL to open when the user presses this button
      url: string,

      // If this key is present, then the URL expires at the
      // given time (1 hour from the time of the initial request).
      // This will be an UTC ISO 8601 datetime, e.g. "2020-07-22T17:58:30Z"
      url_expiry?: string

      // If this key is present, then if the user clicks
      // this button, you MUST hit the `/event/track`
      // endpoint below. Pass this value as the body of the request.
      event_tracking?: any,
    }
  >,
}
```

400 Response format:

```typescript
{
  // The key here is the name of a field from the POST (e.g. "first_name")
  // and the value is an array of validation errors.
  //
  // The key may also be the special value "non_field_errors", which is for
  // errors that don't correspond to a particular field.
  [string]: Array<string>
}
```

### `POST /v1/event/track/`

Auth: No authentication

Body: pass a JSON body with the data present in the `event_tracking`.

On success, the server will return a `201` response.

On an invalid request, the server will return a `4xx` response:

The user should still be directed to the button's target URL, even if the server returns `4xx` (although you should log these failures for later inspection).
