from phonenumber_field.phonenumber import PhoneNumber

from common.pdf.lambdahelpers import (
    BASE64_PDF_CACHE,
    MAX_FIELD_LEN,
    clean_data,
    serialize_template,
)


def test_clean_data():
    assert clean_data(
        {
            "A": 1,
            "B": None,
            "C": 2.2,
            "D": b"foo\0bar",
            "E": "foo\0bar\nbaz",
            "F": "x" * MAX_FIELD_LEN * 2,
            "G": set(),
            "H": [],
            "I": {},
            "J": PhoneNumber.from_string("+16175551234"),
            "K": "Hagåtña",
        }
    ) == {
        "A": 1,
        "B": None,
        "C": 2.2,
        "D": "foobar",
        "E": "foobar\nbaz",
        "F": "x" * MAX_FIELD_LEN,
        "G": "set()",
        "H": "[]",
        "I": "{}",
        "J": "(617) 555-1234",
        "K": "Hagatna",
    }
