"""Tests for views.py."""

import pytest

import ckanext.harvestportal.validators as validators


import ckan.plugins.toolkit as tk


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.usefixtures("with_plugins")
def test_harvestportal_blueprint(app, reset_db):
    resp = app.get(tk.h.url_for("harvestportal.page"))
    assert resp.status_code == 200
    assert resp.body == "Hello, harvestportal!"
