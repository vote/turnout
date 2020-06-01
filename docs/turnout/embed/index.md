# VoteAmerica Tool Embeds

All VoteAmerica tools can be embedded in other websites with a short snippet of code. This will load our tool asynchronously via Javascript into a div with the class `voteamerica-embed`. This will not block rendering of the parent page, and the iframe will check the URL of the parent page for [tracking URL arguments](/embed/tracking/).

The tools have minimal branding, and the fonts and color scheme should work with any website design.

---

You can find your custom embed code via the VoteAmerica admin at [https://admin.voteamerica.com/](https://admin.voteamerica.com/)

If you do not have a subscription to log in there, you can use the generic embeds below.

!!! warning
    **If you use code found on this page, VoteAmerica will never be able to provide you with an export of your data or be able to reliably tell you how many people used the tools on your website.**
    Subscribers should *always* use the source code found by logging into the VoteAmerica admin.

```html
<script src="https://cdn.voteamerica.com/embed/tools.js" async></script>
<div class="voteamerica-embed" data-subscriber="public" data-tool="register"></div>
```

```html
<script src="https://cdn.voteamerica.com/embed/tools.js" async></script>
<div class="voteamerica-embed" data-subscriber="public" data-tool="verify"></div>
```

```html
<script src="https://cdn.voteamerica.com/embed/tools.js" async></script>
<div class="voteamerica-embed" data-subscriber="public" data-tool="absentee"></div>
```

```html
<script src="https://cdn.voteamerica.com/embed/tools.js" async></script>
<div class="voteamerica-embed" data-subscriber="public" data-tool="locate"></div>
```

```html
<script src="https://cdn.voteamerica.com/embed/tools.js" async></script>
<div class="voteamerica-embed" data-subscriber="public" data-tool="leo"></div>
```
