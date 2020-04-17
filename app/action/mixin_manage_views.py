from django.conf import settings


class ActionListViewMixin:
    paginate_by = settings.MANAGEMENT_ACTION_PAGINATION_SIZE
