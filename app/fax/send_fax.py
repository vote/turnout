import json
import logging
from datetime import datetime, timezone
from typing import Optional

from django.conf import settings

from common.apm import tracer
from common.aws import sqs_client
from common.enums import FaxStatus
from storage.models import StorageItem

from .api_views import handle_fax_callback

logger = logging.getLogger("fax")


@tracer.wrap()
def send_fax(
    storage_item: StorageItem,
    to: str,
    on_complete_task: str,
    on_complete_task_arg: Optional[str],
) -> None:
    from .models import Fax

    fax = Fax(
        storage_item=storage_item,
        to=to,
        status=FaxStatus.PENDING,
        on_complete_task=on_complete_task,
        on_complete_task_arg=on_complete_task_arg,
    )
    fax.save()

    callback_url = f"{settings.FAX_GATEWAY_CALLBACK_URL}?token={fax.token}"

    if settings.FAX_DISABLE:
        if settings.FAX_OVERRIDE_DEST:
            send_fax = True
            fax_to = settings.FAX_OVERRIDE_DEST
        else:
            send_fax = False
    else:
        send_fax = True
        fax_to = fax.to.as_e164

    if send_fax:
        payload = json.dumps(
            {
                "fax_id": str(fax.uuid),
                "to": str(fax_to),
                "pdf_url": fax.storage_item.file.url,
                "callback_url": callback_url,
            }
        )
        sqs_client.send_message(
            QueueUrl=settings.FAX_GATEWAY_SQS_QUEUE,
            MessageBody=payload,
            MessageGroupId=fax_to,
        )
    else:
        logger.warn(
            f"FAX_DISABLE is true and FAX_OVERRIDE_DEST is not set. Not faxing to {to}: {storage_item.file.url}"
        )

        # Simulate the callback
        handle_fax_callback(
            {
                "fax_id": fax.uuid,
                "message": "Simulated fax successful",
                "timestamp": datetime.now(tz=timezone.utc),
                "status": FaxStatus.SENT,
            },
            fax,
        )
