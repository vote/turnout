from django.core.validators import RegexValidator
from rest_framework.serializers import ValidationError

from election.choices import STATES


def must_be_true_validator(value):
    """Requires value to be True"""
    if value is not True:
        raise ValidationError("Must be true")
    return value


def state_code_validator(code):
    """Validate states by code"""
    if code not in dict(STATES).keys():
        raise ValidationError(f"{code} is not a valid state code")


zip_validator = RegexValidator(r"^[0-9]{5}$", "Zip codes are 5 digits")
