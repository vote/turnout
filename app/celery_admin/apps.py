from django.apps import AppConfig


class CeleryAdminConfig(AppConfig):
    name = "celery_admin"

    def ready(self):
        import celery_admin.celery_admin
