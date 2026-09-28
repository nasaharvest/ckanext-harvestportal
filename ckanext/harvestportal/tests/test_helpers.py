"""Tests for helpers.py."""

import ckanext.harvestportal.helpers as helpers


def test_harvestportal_hello():
    assert helpers.harvestportal_hello() == "Hello, harvestportal!"


def test_harvestportal_robots_meta(app):
    with app.flask_app.test_request_context("/dataset/?page=3"):
        assert helpers.harvestportal_robots_meta() is None
    with app.flask_app.test_request_context("/dataset/?res_format=CSV"):
        assert helpers.harvestportal_robots_meta() == "noindex, nofollow"
    with app.flask_app.test_request_context(
        "/dataset/", environ_base={"CKAN_LANG_IS_DEFAULT": False}
    ):
        assert helpers.harvestportal_robots_meta() == "noindex, nofollow"
