"""Tests for compress.py."""

import brotli
import pytest
from flask import Blueprint, Flask, Response

from ckanext.harvestportal.compress import init_compress


BIG_JSON = '{"rows": [' + ",".join(['{"a": 1}'] * 500) + "]}"


@pytest.fixture
def flask_client():
    app = Flask(__name__)
    datastore = Blueprint("datastore", __name__)

    @app.route("/page")
    def page():
        return Response(BIG_JSON, mimetype="application/json")

    @datastore.route("/datastore/dump/<rid>")
    def dump(rid):
        return Response(iter([BIG_JSON]), mimetype="application/json")

    app.register_blueprint(datastore)
    init_compress(app)
    return app.test_client()


def test_compresses_when_client_accepts(flask_client):
    resp = flask_client.get("/page", headers={"Accept-Encoding": "gzip, br"})
    assert resp.headers["Content-Encoding"] == "br"
    assert brotli.decompress(resp.data).decode() == BIG_JSON


def test_falls_back_to_gzip(flask_client):
    resp = flask_client.get("/page", headers={"Accept-Encoding": "gzip"})
    assert resp.headers["Content-Encoding"] == "gzip"


def test_no_compression_without_accept_encoding(flask_client):
    resp = flask_client.get("/page")
    assert "Content-Encoding" not in resp.headers
    assert resp.get_data(as_text=True) == BIG_JSON


def test_skips_datastore_dumps(flask_client):
    resp = flask_client.get(
        "/datastore/dump/abc", headers={"Accept-Encoding": "gzip, br"}
    )
    assert "Content-Encoding" not in resp.headers
    assert resp.get_data(as_text=True) == BIG_JSON


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.usefixtures("with_plugins")
def test_ckan_static_file_compressed(app):
    resp = app.get("/harvestportal.css", headers={"Accept-Encoding": "br"})
    assert resp.headers.get("Content-Encoding") == "br"


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.ckan_config("ckanext.harvestportal.compress", "false")
@pytest.mark.usefixtures("with_plugins")
def test_ckan_compression_can_be_disabled(app):
    resp = app.get("/harvestportal.css", headers={"Accept-Encoding": "br"})
    assert "Content-Encoding" not in resp.headers
