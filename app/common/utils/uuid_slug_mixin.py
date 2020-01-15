from django.http import Http404


class UUIDSlugMixin(object):
    def get_object(self, *args, **kwargs):
        try:
            django_object = super(UUIDSlugMixin, self).get_object(*args, **kwargs)
        except ValueError as value_error:
            if str(value_error) == "bytes is not a 16-char string":
                raise Http404
            raise
        except TypeError as type_error:
            if str(type_error) == "Incorrect padding":
                raise Http404
            raise

        return django_object
