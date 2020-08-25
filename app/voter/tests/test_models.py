import datetime

import pytest

from voter.models import Voter


@pytest.mark.parametrize(
    "orig,update,final",
    [
        # successful updates
        (
            (None, None, None),
            (True, datetime.date(2000, 1, 1), None),
            (True, datetime.date(2000, 1, 1), datetime.date(2000, 1, 1)),
        ),
        (
            (None, None, None),
            (True, datetime.date(2000, 1, 1), datetime.date(2020, 2, 2)),
            (True, datetime.date(2000, 1, 1), datetime.date(2020, 2, 2)),
        ),
        (
            (True, datetime.date(2000, 1, 1), datetime.date(2020, 2, 2)),
            (True, datetime.date(2000, 1, 1), datetime.date(2020, 2, 2)),
            (True, datetime.date(2000, 1, 1), datetime.date(2020, 2, 2)),
        ),
        (
            (True, datetime.date(2000, 1, 1), datetime.date(2020, 2, 2)),
            (True, datetime.date(2000, 1, 1), datetime.date(2020, 4, 2)),
            (True, datetime.date(2000, 1, 1), datetime.date(2020, 4, 2)),
        ),
        (
            (None, None, datetime.date(2010, 1, 1)),
            (True, datetime.date(2010, 1, 1), datetime.date(2020, 1, 2)),
            (True, datetime.date(2010, 1, 1), datetime.date(2020, 1, 2)),
        ),
        # updates that should be ignored
        (
            (True, datetime.date(2000, 1, 1), datetime.date(2020, 2, 2)),
            (True, datetime.date(2000, 1, 1), datetime.date(2020, 1, 2)),
            (True, datetime.date(2000, 1, 1), datetime.date(2020, 2, 2)),
        ),
        (
            (True, datetime.date(2010, 1, 1), datetime.date(2020, 2, 2)),
            (True, datetime.date(2000, 1, 1), datetime.date(2020, 1, 2)),
            (True, datetime.date(2010, 1, 1), datetime.date(2020, 2, 2)),
        ),
        (
            (None, None, datetime.date(2020, 3, 1)),
            (True, datetime.date(2010, 1, 1), datetime.date(2020, 1, 2)),
            (None, None, datetime.date(2020, 3, 1)),
        ),
        (
            # older data showing newer registration
            (True, datetime.date(2000, 1, 1), datetime.date(2020, 2, 2)),
            (True, datetime.date(2010, 1, 1), datetime.date(2020, 1, 2)),
            (True, datetime.date(2000, 1, 1), datetime.date(2020, 2, 2)),
        ),
        # unregistered (update)
        (
            (True, datetime.date(2000, 1, 1), datetime.date(2020, 2, 2)),
            (False, None, datetime.date(2020, 4, 2)),
            (False, None, datetime.date(2020, 4, 2)),
        ),
        (
            (False, None, datetime.date(2020, 2, 2)),
            (False, None, datetime.date(2020, 4, 2)),
            (False, None, datetime.date(2020, 4, 2)),
        ),
        # unregistered (do not update)
        (
            (True, datetime.date(2000, 1, 1), datetime.date(2020, 2, 2)),
            (False, None, datetime.date(2020, 1, 2)),
            (True, datetime.date(2000, 1, 1), datetime.date(2020, 2, 2)),
        ),
        (
            # (we don't know how fresh/unfresh this is)
            (True, datetime.date(2000, 1, 1), datetime.date(2000, 1, 1)),
            (False, None, datetime.date(2020, 1, 2)),
            (True, datetime.date(2000, 1, 1), datetime.date(2000, 1, 1)),
        ),
    ],
)
def test_refresh_registration_status(orig, update, final):
    # we pass in datetimes in UTC to refresh_registration_status, but
    # the stored registration_date is a date
    def to_datetime(d):
        if d:
            return datetime.datetime(
                d.year, d.month, d.day, tzinfo=datetime.timezone.utc
            )
        else:
            return None

    v = Voter()
    v.registered = orig[0]
    v.registration_date = orig[1]
    v.last_registration_refresh = to_datetime(orig[2])
    v.refresh_registration_status(
        update[0], to_datetime(update[1]), to_datetime(update[2])
    )
    assert v.registered == final[0]
    assert v.registration_date == final[1]
    assert v.last_registration_refresh == to_datetime(final[2])
