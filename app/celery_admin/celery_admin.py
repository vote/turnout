import ast
import logging
import re
from typing import Any, List, Tuple

import sentry_sdk
from django.contrib import admin, messages
from django.template.loader import render_to_string
from django.utils.translation import ngettext
from django_celery_results.admin import TaskResultAdmin
from django_celery_results.models import TaskResult

from turnout.celery_app import app

uuid_re = re.compile(r'UUID\([\'"]([0-9a-f-]+)[\'"]\)')

SUCCESS_MESSAGE_TEMPLATE = "admin/task_success.html"
FAILURE_MESSAGE_TEMPLATE = "admin/task_failure.html"

logger = logging.getLogger("turnout")


def parse_task_args(arg_str: str) -> Any:
    # Convert "UUID(xxx)" to "xxx" -- we pass UUIDs to tasks frequently and they
    # get implicitly converted to strings when passed to Redis (so the task
    # definitions expect them as strings) but they are saved to the Celery
    # result store as Python reprs.
    repr_str = uuid_re.sub(r"'\1'", arg_str)
    print(repr_str, flush=True)
    return ast.literal_eval(repr_str)


class TurnoutTaskResultAdmin(TaskResultAdmin):
    actions = ["rerun"]

    def rerun(self, request, queryset):
        # List of (success, message) pairs
        results: List[Tuple[bool, str]] = []

        # Retry each task
        for task_result in queryset:
            try:
                args = parse_task_args(task_result.task_args)
                kwargs = parse_task_args(task_result.task_kwargs)

                new_id = app.send_task(task_result.task_name, args=args, kwargs=kwargs)
            except Exception as e:
                extra = {"task_id": task_result.pk}
                logger.exception("failed to re-run task %s", extra, extra=extra)

                sentry_sdk.capture_exception(e)

                results.append(
                    (
                        False,
                        render_to_string(
                            FAILURE_MESSAGE_TEMPLATE, {"task": task_result}
                        ),
                    )
                )
            else:
                results.append(
                    (
                        True,
                        render_to_string(
                            SUCCESS_MESSAGE_TEMPLATE,
                            {"task": task_result, "new_task_id": new_id},
                        ),
                    )
                )

        # Generate a summary
        n_success = sum(1 for result in results if result[0])
        n_failure = sum(1 for result in results if not result[0])

        success_message = (
            ngettext(
                "%d task was successfully re-run",
                "%d tasks were successfully re-run",
                n_success,
            )
            % n_success
        )

        failure_message = (
            ngettext(
                "%d task failed to re-run", "%d tasks failed to re-run", n_failure,
            )
            % n_failure
        )

        if n_success and n_failure:
            self.message_user(
                request, f"{failure_message} and {success_message}.", messages.WARNING,
            )
        elif n_failure:
            self.message_user(
                request, f"{failure_message}.", messages.ERROR,
            )
        else:
            self.message_user(
                request, f"{success_message}.", messages.SUCCESS,
            )

        # Also post individual statuses and links
        for was_success, message in results:
            self.message_user(
                request, message, messages.SUCCESS if was_success else messages.ERROR,
            )

    rerun.short_description = "Re-run selected tasks"  # type:ignore


admin.site.unregister(TaskResult)
admin.site.register(TaskResult, TurnoutTaskResultAdmin)
