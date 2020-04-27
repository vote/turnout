from typing import List


class CDNCachedView:
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        if not hasattr(response, "cache_tags"):
            response.cache_tags: List[str] = []

        new_tags = []

        if hasattr(self, "cache_tags"):
            new_tags = new_tags + self.cache_tags

        if hasattr(self, "model"):
            new_tags.append(self.model._meta.app_label)
            new_tags.append(self.model._meta.object_name.lower())

        new_tags.append(self.__class__.__module__)

        if hasattr(self, "object"):
            new_tags.append(str(self.object.pk))
        elif hasattr(self, "kwargs") and "pk" in self.kwargs:
            new_tags.append(str(self.kwargs["pk"]))
        elif hasattr(self, "queryset"):
            values = self.queryset.values_list("pk", flat=True)
            keys = [str(v) for v in values]
            new_tags = new_tags + keys

        response.cache_tags = response.cache_tags + new_tags

        return response
