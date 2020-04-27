import pytest
from model_bakery import baker

from election.models import State


@pytest.mark.django_db
def test_state_count():
    assert State.objects.count() == 51


@pytest.mark.django_db
def test_cdn_clear_information_field(mocker):
    patched_tags_call = mocker.patch("election.models.purge_cdn_tags")
    patched_single_tag_call = mocker.patch("election.models.purge_cdn_tag")
    information = baker.make_recipe("election.markdown_information")

    patched_tags_call.assert_called_once_with(
        ["state", "stateinformationfield", "stateinformationfieldtype",]
    )

    information.text = "New Text"
    information.save()

    assert information.state_id == "XX"
    patched_single_tag_call.assert_called_once_with("XX")
