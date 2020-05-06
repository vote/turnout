import collections
from typing import TYPE_CHECKING, Any, Dict, List, Mapping

from enumfields.drf.serializers import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework.fields import empty

from multi_tenant.mixins_serializers import PartnerSerializerMixin

from .models import Action

if TYPE_CHECKING:
    from rest_framework.utils.model_meta import FieldInfo
    from django.db.models import Model


class ActionSerializer(
    PartnerSerializerMixin, EnumSupportSerializerMixin, serializers.ModelSerializer
):
    action = serializers.PrimaryKeyRelatedField(read_only=True, required=False)
    sms_opt_in_partner = serializers.BooleanField(required=False)

    def __init__(self, instance=None, data=empty, **kwargs) -> None:
        self.incomplete = kwargs.pop("incomplete", False)
        super().__init__(instance=instance, data=data, **kwargs)

    def create(self, validated_data: Dict[(str, Any)]) -> "Model":
        validated_data["action"] = Action.objects.create()
        return super().create(validated_data)

    def get_field_names(
        self, declared_fields: Mapping[(str, serializers.Field)], info: "FieldInfo"
    ) -> List[str]:
        # There are 5 possible Meta attributes for fields in ActionSerializers,
        # "minimum_necessary_fields", "nationally_required_fields", "optional_fields",
        # "fields", and "exclude"
        minimum_necessary_fields = getattr(self.Meta, "minimum_necessary_fields", [])
        nationally_required_fields = getattr(
            self.Meta, "nationally_required_fields", []
        )
        optional_fields = getattr(self.Meta, "optional_fields", [])
        standard_fields = getattr(self.Meta, "fields", [])

        # By default ModelSerializers need a "field" attribute, but we don't want
        # to make a bunch of our code duplicative. So setting our own Meta.fields
        # will give ourselves more flexibility.
        setattr(
            self.Meta,
            "fields",
            minimum_necessary_fields
            + nationally_required_fields
            + optional_fields
            + standard_fields,
        )

        return super().get_field_names(declared_fields, info)

    def get_fields(self) -> "collections.OrderedDict[str, serializers.Field]":
        initial_fields = super().get_fields()
        fields = collections.OrderedDict()
        for key, value in initial_fields.items():
            if key in getattr(self.Meta, "minimum_necessary_fields", []):
                value.required = True  # type: ignore[attr-defined]
            elif not self.incomplete and key in getattr(
                self.Meta, "nationally_required_fields", []
            ):
                value.required = True  # type: ignore[attr-defined]
            else:
                value.required = False  # type: ignore[attr-defined]
            fields[key] = value
        return fields
