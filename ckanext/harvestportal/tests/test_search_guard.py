"""Tests for search_guard.py."""

import pytest
from werkzeug.datastructures import MultiDict

from ckan.tests import factories

from ckanext.harvestportal.search_guard import _filter_count, _has_show_more


def test_filter_count_matches_ckan_search_rules():
    args = MultiDict([
        ("q", "rice"), ("page", "2"), ("sort", "name asc"),
        ("_tags_limit", "0"), ("ext_bbox", "1,2,3,4"),
        ("tags", "flood"), ("tags", "water"), ("res_format", "CSV"),
        ("organization", ""),
    ])
    assert _filter_count(args) == 3


FOUR = "/dataset/?tags=a&tags=b&res_format=CSV&license_id=cc-by"
THREE = "/dataset/?tags=a&tags=b&res_format=CSV"


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
@pytest.mark.parametrize("url,status", [
    (THREE, 200),
    (FOUR, 400),
    ("/es" + FOUR, 400),
    ("/dataset/?q=rice&page=3&sort=name+asc", 200),
])
def test_search_page(app, url, status):
    resp = app.get(url, status=status)
    assert ("Too many search filters" in resp.body) == (status == 400)


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_api_search_not_affected(app):
    resp = app.get(
        "/api/3/action/package_search",
        query_string={
            "fq": "tags:a AND tags:b AND res_format:CSV AND license_id:cc-by",
            "rows": 1,
        },
        status=200,
    )
    assert resp.json["success"]


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.ckan_config("ckanext.harvestportal.search_max_filters", "5")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_threshold_configurable(app):
    app.get(FOUR, status=200)


def test_has_show_more():
    assert _has_show_more(MultiDict([("_tags_limit", "0")]))
    assert _has_show_more(MultiDict([("tags", "a"), ("_res_format_limit", "0")]))
    assert not _has_show_more(MultiDict([("tags", "a"), ("_limit", "0"), ("page", "2")]))


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
@pytest.mark.parametrize("query,status", [
    ("", 200),                                                   # plain page
    ("?_tags_limit=0", 200),                                     # Show more, no filters
    ("?tags=a&tags=b&_tags_limit=0", 200),                       # Show more, 2 filters
    ("?tags=a&tags=b&res_format=CSV&_tags_limit=0", 400),        # Show more, 3 filters
    ("?tags=a&tags=b&res_format=CSV", 200),                      # 3 filters
    ("?tags=a&tags=b&res_format=CSV&license_id=cc-by", 400),     # 4 filters
])
@pytest.mark.parametrize("page", ["dataset", "organization", "group"])
def test_guarded_pages(app, page, query, status):
    if page == "dataset":
        path = "/dataset/"
    elif page == "organization":
        path = "/organization/" + factories.Organization()["name"]
    else:
        path = "/group/" + factories.Group()["name"]
    resp = app.get(path + query, status=status)
    assert ("Too many search filters" in resp.body) == (status == 400)


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_translated_org_page_guarded(app):
    org = factories.Organization()["name"]
    app.get(f"/es/organization/{org}?tags=a&tags=b&res_format=CSV&_tags_limit=0", status=400)


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.ckan_config("ckanext.harvestportal.show_more_max_filters", "3")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_show_more_threshold_configurable(app):
    app.get("/dataset/?tags=a&tags=b&res_format=CSV&_tags_limit=0", status=200)
