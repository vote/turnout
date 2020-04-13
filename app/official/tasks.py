from celery import shared_task


@shared_task
def sync_usvotefoundation():
    from .usvf_sync import sync

    sync()
