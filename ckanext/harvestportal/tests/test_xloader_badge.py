"""Tests for the xloader_badge wrapper: no badges in dataset resource lists."""

import pytest

from ckan.tests import factories, helpers

PLUGINS = "datastore xloader harvestportal"


@pytest.fixture
def failed_load():
    """A CSV resource whose last xloader job failed, so xloader shows a badge."""
    dataset = factories.Dataset()
    resource = factories.Resource(package_id=dataset["id"], format="CSV",
                                  url="https://example.org/data.csv")
    helpers.call_action(
        "task_status_update", entity_id=resource["id"], entity_type="resource",
        task_type="xloader", key="xloader", value="{}", state="error",
        error="{}", last_updated="2026-10-27T12:00:00")
    return dataset, resource


@pytest.mark.ckan_config("ckan.plugins", PLUGINS)
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
class TestXloaderBadge:

    def test_no_badge_on_dataset_page(self, app, failed_load):
        dataset, resource = failed_load
        body = app.get(f"/dataset/{dataset['name']}").body
        assert resource["id"] in body  # the resource is still listed
        assert "loader-badge" not in body

    def test_badge_still_on_resource_page(self, app, failed_load):
        dataset, resource = failed_load
        body = app.get(f"/dataset/{dataset['name']}/resource/{resource['id']}").body
        assert "loader-badge" in body
