"""Tests for views.py."""

import pytest

import ckan.plugins.toolkit as tk


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.usefixtures("with_plugins")
def test_harvestportal_blueprint(app, reset_db):
    resp = app.get(tk.h.url_for("harvestportal.page"))
    assert resp.status_code == 200
    assert resp.body == "Hello, harvestportal!"


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.usefixtures("with_plugins")
def test_health(app):
    resp = app.get("/health")
    assert resp.status_code == 200
    assert resp.body == "OK"


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.usefixtures("with_plugins")
def test_robots_txt_blocks_dumps_and_facets(app):
    body = app.get("/robots.txt").body
    assert "Disallow: /api/" in body
    assert "Disallow: /datastore/dump/" in body
    assert "Disallow: /*?*tags=" in body


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
@pytest.mark.parametrize("url,noindex", [
    ("/dataset/", False),
    ("/dataset/?page=2", False),
    ("/dataset/?tags=flood", True),
    ("/es/dataset/", True),
])
def test_robots_meta(app, url, noindex):
    body = app.get(url).body
    assert ('<meta name="robots" content="noindex, nofollow"' in body) == noindex


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.usefixtures("with_plugins")
def test_robots_txt_blocks_activity_pages(app):
    body = app.get("/robots.txt").body
    assert "Disallow: /dataset/activity/" in body
    assert "Disallow: /organization/activity/" in body
    assert "Disallow: /user/activity/" in body


@pytest.mark.ckan_config("ckan.plugins", "activity harvestportal")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_activity_pages_are_noindex(app, migrate_db_for):
    from ckan.tests import factories
    migrate_db_for("activity")
    dataset = factories.Dataset()
    org = factories.Organization()
    for url in [f"/dataset/activity/{dataset['name']}",
                f"/organization/activity/{org['name']}"]:
        resp = app.get(url)
        assert resp.status_code == 200
        assert '<meta name="robots" content="noindex, nofollow"' in resp.body
    body = app.get(f"/dataset/{dataset['name']}").body
    assert '<meta name="robots" content="noindex, nofollow"' not in body
