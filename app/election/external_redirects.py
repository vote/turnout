import logging

from django.conf import settings

from common.aws import s3_client

from .models import State, StateInformation

URL_PREFIX = "state-redirect"

SLUG_FALLBACK_URLS = {
    "external_tool_verify_status": "https://voteamerica.com/am-i-registered-to-vote",
    "external_tool_ovr": "https://voteamerica.com/register-to-vote",
    "external_tool_vbm_application": "https://voteamerica.com/absentee-ballot",
    "external_tool_polling_place": "https://www.voteamerica.com/where-is-my-polling-place",
    "external_tool_absentee_ballot_tracker": "https://www.voteamerica.com/vote-by-mail-ballot-tracker/",
}


logger = logging.getLogger("election")


def publish():
    bucket = settings.STATE_TOOL_REDIRECT_BUCKET

    for state in State.states.all():
        for slug, fallback in SLUG_FALLBACK_URLS.items():
            item = StateInformation.objects.get(state=state, field_type__slug=slug)
            if item and item.text:
                target = item.text
            else:
                target = fallback

            objname = f"{URL_PREFIX}/{item.state.code}/{item.field_type}"
            logger.info(objname)
            response = s3_client.put_object(
                Bucket=bucket,
                Key=objname,
                WebsiteRedirectLocation=target,
                ACL="public-read",
            )
            if response.get("ResponseMetadata", {}).get("HTTPStatusCode") != 200:
                logger.warning("Unable to push {objname} to {bucket}")
