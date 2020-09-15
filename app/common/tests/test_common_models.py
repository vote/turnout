import datetime

import pytest

from common.models import DelayedTask


@pytest.mark.django_db
def test_schedule():
    t = DelayedTask.schedule(
        datetime.datetime(2020, 1, 2, 3, 5, 5).replace(tzinfo=datetime.timezone.utc),
        "foo",
        "a1",
        "a2",
        kw1=1,
        kw2=3,
    )

    assert t.due_at == datetime.datetime(2020, 1, 2, 3, 5, 5).replace(
        tzinfo=datetime.timezone.utc
    )
    assert t.task_name == "foo"
    assert t.args == ["a1", "a2"]
    assert t.kwargs == {"kw1": 1, "kw2": 3}


@pytest.mark.django_db
def test_schedule_polite():
    now = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
    t = DelayedTask.schedule_polite("XX", "foo", 1, 2, kw1=1, kw2=3)

    assert t.due_at.hour >= 17
    assert t.due_at >= now
    assert t.task_name == "foo"
    assert t.args == [1, 2]
    assert t.kwargs == {"kw1": 1, "kw2": 3}


@pytest.mark.django_db
def test_schedule_days_later_polite():
    now = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
    t = DelayedTask.schedule_days_later_polite("XX", 2, "foo", 1, 2, kw1=1, kw2=4)

    assert t.due_at > now + datetime.timedelta(days=1)
    assert t.due_at.hour >= 17
    assert t.task_name == "foo"
    assert t.args == [1, 2]
    assert t.kwargs == {"kw1": 1, "kw2": 4}


@pytest.mark.django_db
def test_schedule_tomorrow_polite():
    now = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
    t = DelayedTask.schedule_tomorrow_polite("XX", "foo", 1, 2, kw1=1, kw2=5)

    assert t.due_at > now
    assert t.due_at.hour == 17
    assert t.task_name == "foo"
    assert t.args == [1, 2]
    assert t.kwargs == {"kw1": 1, "kw2": 5}
