from rest_framework import serializers

from .models import Address, Office, Region


class RegionNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ("name", "external_id")


class AddressSerializer(serializers.ModelSerializer):
    lat = serializers.SerializerMethodField("get_lat")
    lng = serializers.SerializerMethodField("get_lng")

    def get_lat(self, address):
        if address.location:
            return address.location.y
        return None

    def get_lng(self, address):
        if address.location:
            return address.location.x
        return None

    class Meta:
        model = Address
        fields = [
            "address",
            "address2",
            "address3",
            "city",
            "state",
            "zipcode",
            "location",
            "website",
            "email",
            "phone",
            "fax",
            "is_physical",
            "is_regular_mail",
            "process_domestic_registrations",
            "process_absentee_requests",
            "process_absentee_ballots",
            "process_overseas_requests",
            "process_overseas_ballots",
            "lat",
            "lng",
        ]


class OfficeSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(source="address_set", many=True)

    class Meta:
        model = Office
        fields = ("hours", "notes", "addresses")


class RegionDetailSerializer(serializers.ModelSerializer):
    offices = OfficeSerializer(source="office_set", many=True)

    class Meta:
        model = Region
        fields = ["external_id", "name", "county", "municipality", "offices"]
