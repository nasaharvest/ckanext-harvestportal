import ckan.plugins.toolkit as toolkit


def harvestportal_hello():
    return "Hello, harvestportal!"


def harvestportal_dataset_count():
    return toolkit.get_action("package_search")({}, {"rows": 0})["count"]


def harvestportal_organization_count():
    return len(toolkit.get_action("organization_list")({}, {"all_fields": False}))


def harvestportal_group_count():
    return len(toolkit.get_action("group_list")({}, {"all_fields": False}))


def get_helpers():
    return {
        "harvestportal_hello": harvestportal_hello,
        "harvestportal_dataset_count": harvestportal_dataset_count,
        "harvestportal_organization_count": harvestportal_organization_count,
        "harvestportal_group_count": harvestportal_group_count,
    }
