"""Tests for export_guard.py: data exports need a signed-in user."""

import re
from urllib.parse import parse_qs, urlsplit

import pytest

from ckan.tests import factories, helpers

PLUGINS = "datastore harvestportal"
BROWSER = {"Accept": "text/html,application/xhtml+xml,*/*;q=0.8"}


@pytest.fixture
def table():
    dataset = factories.Dataset()
    result = helpers.call_action(
        "datastore_create", resource={"package_id": dataset["id"]}, force=True,
        fields=[{"id": "Country", "type": "text"}],
        records=[{"Country": "Kenya"}, {"Country": "Mali"}])
    return dataset, result["resource_id"]


@pytest.mark.ckan_config("ckan.plugins", PLUGINS)
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
class TestExportGuard:

    def test_anonymous_browser_sent_to_login_and_back(self, app, table):
        _, rid = table
        resp = app.get(f"/datastore/dump/{rid}?format=json", headers=BROWSER,
                       follow_redirects=False)
        assert resp.status_code == 302
        loc = urlsplit(resp.headers["Location"])
        assert loc.path == "/user/login"
        assert parse_qs(loc.query)["came_from"] == [f"/datastore/dump/{rid}?format=json"]

    def test_anonymous_script_gets_401(self, app, table):
        _, rid = table
        resp = app.get(f"/datastore/dump/{rid}", headers={"Accept": "*/*"},
                       follow_redirects=False)
        assert resp.status_code == 401
        assert "API token" in resp.body

    def test_api_token_user_can_download(self, app, table):
        _, rid = table
        user = factories.User()
        token = factories.APIToken(user=user["name"])
        resp = app.get(f"/datastore/dump/{rid}",
                       headers={"Authorization": token["token"]})
        assert resp.status_code == 200
        assert "Kenya" in resp.body and "Mali" in resp.body

    def test_previews_and_api_still_anonymous(self, app, table):
        _, rid = table
        resp = app.get("/api/3/action/datastore_search",
                       query_string={"resource_id": rid})
        assert resp.status_code == 200
        assert resp.json["result"]["total"] == 2

    def test_login_page_passes_came_from_to_single_sign_on(self, app):
        body = app.get("/user/login",
                       query_string={"came_from": "/datastore/dump/abc?format=json"}).body
        assert "/user/login/oidc-pkce?came_from=/datastore/dump/abc%3Fformat%3Djson" in body

    @pytest.mark.parametrize("bad", ["https://evil.example/x", "//evil.example/x", "javascript:alert(1)"])
    def test_login_page_ignores_offsite_came_from(self, app, bad):
        body = app.get("/user/login", query_string={"came_from": bad}).body
        # (CKAN's language menu echoes the page URL elsewhere; only the
        # single sign-on link matters here.)
        sso = re.findall(r'href="([^"]*/oidc-pkce[^"]*)"', body)
        assert sso and all(link == "/user/login/oidc-pkce" for link in sso)


@pytest.mark.ckan_config("ckan.plugins", PLUGINS)
@pytest.mark.ckan_config("ckanext.harvestportal.require_login_for_exports", "false")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_can_be_turned_off(app, table):
    dataset, rid = table
    assert app.get(f"/datastore/dump/{rid}", headers={"Accept": "*/*"}).status_code == 200
