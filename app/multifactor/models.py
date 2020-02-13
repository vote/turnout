from base64 import b32encode
from binascii import unhexlify
from urllib.parse import quote, urlencode

from django.conf import settings
from django.db import models
from django_otp.models import Device as OTPDevice
from django_otp.models import ThrottlingMixin
from django_otp.oath import TOTP
from django_otp.util import hex_validator, random_hex

from common.utils.models import TimestampModel, UUIDModel


def default_key():
    return random_hex(20)


def key_validator(value):
    return hex_validator()(value)


class Device(OTPDevice):
    confirmed = models.BooleanField(default=False)

    class Meta(object):
        abstract = True


class UUIDTOTPDevice(ThrottlingMixin, TimestampModel, UUIDModel, Device):
    key = models.TextField(
        validators=[key_validator],
        default=default_key,
        help_text="A hex-encoded secret key of up to 40 bytes.",
    )
    digits = models.PositiveSmallIntegerField(
        default=settings.MULTIFACTOR_DIGITS_DEFAULT,
        help_text="The number of digits to expect in a token.",
    )
    start_time = models.BigIntegerField(
        default=0, help_text="The Unix time at which to begin counting steps."
    )
    last_time = models.BigIntegerField(
        default=-1,
        help_text="The t value of the latest verified token. The next token must be at a higher time step.",
    )
    step = models.PositiveSmallIntegerField(
        default=settings.MULTIFACTOR_STEP_LENGTH, help_text="The time step in seconds."
    )

    class Meta(Device.Meta):
        verbose_name = "TOTP device"
        ordering = ["-created_at"]

    @property
    def bin_key(self):
        return unhexlify(self.key.encode())

    def verify_token(self, token):
        verify_allowed, _ = self.verify_is_allowed()
        if not verify_allowed:
            return False

        try:
            token = int(token)
        except Exception:
            verified = False
        else:
            key = self.bin_key

            totp = TOTP(key, step=self.step, t0=self.start_time, digits=self.digits)
            verified = totp.verify(
                token,
                tolerance=settings.MULTIFACTOR_TOLERANCE,
                min_t=self.start_time + 1,
            )
            if verified:
                self.last_time = totp.t()
                self.throttle_reset(commit=False)
                self.save()

        if not verified:
            self.throttle_increment(commit=True)

        return verified

    def get_throttle_factor(self):
        return settings.MULTIFACTOR_THROTTLE_FACTOR

    @property
    def config_url(self):
        # From https://github.com/google/google-authenticator/wiki/Key-Uri-Format
        issuer = settings.MULTIFACTOR_ISSUER.replace(":", "")
        label = f"{issuer}:{self.user.get_username()}"
        url_params = {
            "issuer": issuer,
            "secret": b32encode(self.bin_key),
            "algorithm": "SHA1",
            "digits": self.digits,
            "period": self.step,
        }
        return f"otpauth://totp/{quote(label)}?{urlencode(url_params)}"
