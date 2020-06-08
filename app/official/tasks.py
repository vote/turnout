from celery import shared_task


@shared_task
def sync_usvotefoundation():
    from .usvf import sync, check_vbm_states

    sync()
    check_vbm_states()
