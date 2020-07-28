# Events and Google Tag Manager

VoteAmerica uses JavaScript event tracking and we pass these events up to the parent window of embeds.

These events are These events can be consumed by the parent window with a little bit of JavaScript. These events have a type of `VoteAmericaEvent` and can be listened for using the following JavaScript snippet.

```js
window.addEventListener('VoteAmericaEvent', function(evt) {
  console.log(evt); // This can be replaced with any function
});
```

## Using Google Tag Manager

[Google Tag Manager (GTM)](https://marketingplatform.google.com/about/tag-manager/) is a system from Google that allows you to manage website tags. If you have GTM installed on your website, you can send the VoteAmerica events to GTM using the following JavaScript snippet.

```js
window.dataLayer = window.dataLayer || [];
window.addEventListener('VoteAmericaEvent', function(evt) {
  dataLayer.push(evt.detail.data);
});
```

Once the events are sent to GTM, you'll need to set up triggers for your tags there. [Google has documentation on that here.](https://support.google.com/tagmanager/answer/6106716?hl=en)

## VoteAmerica Events

Here's a list of events provided by VoteAmerica. Some events have variable parameters, such as a state or url. Those variable parameters are denoted using double braces. Here is an example `{{ state }}`.

### Verify Tool

```js
{
  event: 'action-finish',
  tool: 'verify',
  state: {{ state }},
}
```
### Register

```js
{
  event: 'action-start',
  tool: 'register',
  state: {{ state }},
}

{
  event: 'action-finish',
  method: 'external',
  tool: 'register',
  url: {{ external url }},
  state: {{ state }},
}

{
  event: 'action-finish',
  method: 'pdf',
  tool: 'register',
  state: {{ state }},
}
```

### Absentee Tool

```js
{
  event: 'action-start',
  tool: 'absentee',
  state: {{ state }},
}

{
  event: 'action-finish',
  method: 'pdf',
  tool: 'absentee',
  state: {{ state }},
}

{
  event: 'action-finish',
  method: 'external',
  tool: 'absentee',
  url: {{ external link }},
  state: {{ state }},
}

{
  event: 'action-finish',
  method: 'external-confirmed',
  tool: 'absentee',
  url: {{ external link }},
  state: {{ state }},
}

{
  event: 'action-finish',
  method: 'fax',
  tool: 'absentee',
  state: {{ state }},
}

{
  event: 'action-finish',
  method: 'email',
  tool: 'absentee',
  state: {{ state }},
}

{
  event: 'action-finish',
  method: 'pdf',
  tool: 'absentee',
  state: {{ state }},
}

{
  event: 'action-restart',
  tool: 'absentee',
}
```

### LEO Lookup Tool

```js
{
  event: 'action-finish',
  tool: 'leo',
  state: {{ state }},
}
```

### Locate Tool

```js
{
  event: 'action-finish',
  tool: 'locator',
  state: {{ state }},
}
```
