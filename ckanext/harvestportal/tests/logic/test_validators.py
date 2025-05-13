"""Tests for validators.py."""

import pytest

import ckan.plugins.toolkit as tk

from ckanext.harvestportal.logic import validators


def test_harvestportal_reauired_with_valid_value():
    assert validators.harvestportal_required("value") == "value"


def test_harvestportal_reauired_with_invalid_value():
    with pytest.raises(tk.Invalid):
        validators.harvestportal_required(None)
