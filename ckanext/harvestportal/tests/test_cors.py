"""Tests for cors.py."""

import pytest

PREFLIGHT = {
    "Origin": "https://dashboard.example.org",
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type",
}


def _preflight(app):
    return app.options("/api/3/action/status_show", headers=PREFLIGHT)


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.ckan_config("ckan.cors.origin_allow_all", True)
@pytest.mark.usefixtures("with_plugins")
def test_preflight_is_cacheable(app):
    resp = _preflight(app)
    assert resp.headers["Access-Control-Max-Age"] == "7200"
    assert resp.headers["Access-Control-Allow-Origin"] == "*"


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.ckan_config("ckan.cors.origin_allow_all", True)
@pytest.mark.usefixtures("with_plugins")
def test_other_requests_unchanged(app):
    resp = app.get("/api/3/action/status_show",
                   headers={"Origin": PREFLIGHT["Origin"]})
    assert resp.status_code == 200
    assert "Access-Control-Max-Age" not in resp.headers
    assert resp.headers["Access-Control-Allow-Origin"] == "*"


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.ckan_config("ckan.cors.origin_allow_all", True)
@pytest.mark.ckan_config("ckanext.harvestportal.cors_max_age", "0")
@pytest.mark.usefixtures("with_plugins")
def test_can_be_disabled(app):
    assert "Access-Control-Max-Age" not in _preflight(app).headers
