import string
import unicodedata

ALLOWED_CHARACTERS = string.ascii_letters + string.digits + " -.,#"
# allow only letters, digits and simple punctuation


def remove_special_characters(s):
    # first convert to ascii (replace accents with plain chars)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    # then remove anything which is not an allowed character
    s = "".join(c for c in s if c in ALLOWED_CHARACTERS)
    return s.strip()


class StringFormatter(string.Formatter):
    def __init__(self, missing="", bad_fmt="!!"):
        self.missing, self.bad_fmt = missing, bad_fmt

    def get_field(self, field_name, args, kwargs):
        # Handle missing key replacement
        try:
            val = super(StringFormatter, self).get_field(field_name, args, kwargs)
        except (KeyError, AttributeError):
            val = None, field_name
        return val

    def format_field(self, value, spec):
        # handle an invalid format
        if value == None:
            return self.missing
        try:
            return super(StringFormatter, self).format_field(value, spec)
        except ValueError:
            if self.bad_fmt is not None:
                return self.bad_fmt
            else:
                raise
