from typing import Any, Dict

from django.conf import settings

EMAIL_RETRY_PROPS: Dict[str, Any] = {
    "autoretry_for": (Exception,),
    "retry_kwargs": {"max_retries": settings.EMAIL_TASK_RETRIES},
    "retry_backoff": settings.EMAIL_TASK_RETRY_BACKOFF,
    "retry_backoff_max": settings.EMAIL_TASK_RETRY_BACKOFF_MAX,
    "retry_jitter": settings.EMAIL_TASK_RETRY_JITTER,
}
