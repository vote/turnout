from django.conf import settings


class ActionListViewMixin:
    paginate_by = settings.MANAGEMENT_ACTION_PAGINATION_SIZE

    def get_queryset(self):
        queryset = super().get_queryset()

        search_query = self.request.GET.get("q")
        if search_query:
            queryset = queryset.filter(search=search_query)

        return queryset
