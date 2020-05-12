class PartnerGenericViewMixin:
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(partner__default_slug__slug=self.kwargs["partner"])
        )
