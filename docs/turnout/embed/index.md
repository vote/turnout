# VoteAmerica Tool Embeds

All VoteAmerica tools can be embedded in other websites with a short snippet of code. This will load our tool asynchronously via Javascript into a div with the class `voteamerica-embed`. This will not block rendering of the parent page, and the iframe will check the URL of the parent page for [UTM parameters](/embed/tagmanager) or source tracking,

The tools have minimal branding, and the fonts and color scheme should work with any website design.

You can also view examples of the various embeded tools at 

---

You can find your custom embed code via the VoteAmerica admin at [https://admin.voteamerica.com/](https://admin.voteamerica.com/)

If you do not have a subscription to log in there, you can use the generic embeds below. 

```html
<script src="https://cdn.voteamerica.com/embed/partner.js" async></script>
<div class="voteamerica-embed" data-partner="voteamerica" data-tool="register"></div>
```

```html
<script src="https://cdn.voteamerica.com/embed/partner.js" async></script>
<div class="voteamerica-embed" data-partner="voteamerica" data-tool="verify"></div>
```

```html
<script src="https://cdn.voteamerica.com/embed/partner.js" async></script>
<div class="voteamerica-embed" data-partner="voteamerica" data-tool="absentee"></div>
```

```html
<script src="https://cdn.voteamerica.com/embed/partner.js" async></script>
<div class="voteamerica-embed" data-partner="voteamerica" data-tool="locate"></div>
```

```html
<script src="https://cdn.voteamerica.com/embed/partner.js" async></script>
<div class="voteamerica-embed" data-partner="voteamerica" data-tool="leo"></div>
```

Please note that you will not be able to track usage of these tools without an active subscription.
