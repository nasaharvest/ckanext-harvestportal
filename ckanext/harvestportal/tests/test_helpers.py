"""Tests for helpers.py."""

import ckanext.harvestportal.helpers as helpers


def test_harvestportal_hello():
    assert helpers.harvestportal_hello() == "Hello, harvestportal!"
