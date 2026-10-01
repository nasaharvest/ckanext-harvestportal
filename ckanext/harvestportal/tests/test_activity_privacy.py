"""Tests for activity_privacy.py."""

import pytest

from ckan.tests import factories

PLUGINS = "activity harvestportal"


@pytest.fixture
def edited_dataset(migrate_db_for):
    migrate_db_for("activity")
    editor = factories.Sysadmin(fullname="Editor Fullname")
    dataset = factories.Dataset(user=editor, notes="first")
    return editor, dataset


def _activities(app, dataset, headers=None):
    resp = app.get(
        "/api/3/action/package_activity_list",
        query_string={"id": dataset["id"]},
        headers=headers or {},
    )
    return resp.json["result"]


@pytest.mark.ckan_config("ckan.plugins", PLUGINS)
@pytest.mark.ckan_config("ckan.auth.public_user_details", False)
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_anonymous_does_not_see_editor(app, edited_dataset):
    editor, dataset = edited_dataset

    body = app.get(f"/dataset/activity/{dataset['name']}").body
    assert "Editor Fullname" not in body
    assert editor["name"] not in body
    assert "A Harvest Portal user" in body

    activities = _activities(app, dataset)
    assert activities
    for activity in activities:
        assert activity["user_id"] is None
        assert activity["data"].get("actor") is None


@pytest.mark.ckan_config("ckan.plugins", PLUGINS)
@pytest.mark.ckan_config("ckan.auth.public_user_details", False)
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_logged_in_user_sees_editor(app, edited_dataset):
    editor, dataset = edited_dataset
    token = factories.APIToken(user=editor["name"])
    headers = {"Authorization": token["token"]}

    body = app.get(
        f"/dataset/activity/{dataset['name']}", headers=headers).body
    assert "Editor Fullname" in body

    activities = _activities(app, dataset, headers)
    assert activities[0]["user_id"] == editor["id"]
    assert activities[0]["data"]["actor"] == editor["name"]


@pytest.mark.ckan_config("ckan.plugins", PLUGINS)
@pytest.mark.ckan_config("ckan.auth.public_user_details", True)
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_public_user_details_shows_editor(app, edited_dataset):
    editor, dataset = edited_dataset

    body = app.get(f"/dataset/activity/{dataset['name']}").body
    assert "Editor Fullname" in body
    assert _activities(app, dataset)[0]["user_id"] == editor["id"]


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.usefixtures("with_plugins")
def test_works_without_activity_plugin(app):
    assert app.get("/dataset/").status_code == 200
