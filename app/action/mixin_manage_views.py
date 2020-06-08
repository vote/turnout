from django.conf import settings
from django.contrib.postgres.search import SearchVector


class ActionListViewMixin:
    paginate_by = settings.MANAGEMENT_ACTION_PAGINATION_SIZE

    def get_queryset(self):
        queryset = super().get_queryset()

        search_query = self.request.GET.get("q")
        if search_query:
            queryset = queryset.annotate(
                search=SearchVector("first_name", "last_name", "email")
            ).filter(search=search_query)

        return queryset
