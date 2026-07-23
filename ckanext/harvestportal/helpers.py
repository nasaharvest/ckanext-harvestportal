import ckan.plugins.toolkit as toolkit


def harvestportal_hello():
    return "Hello, harvestportal!"


def harvestportal_dataset_count():
    # include_private defaults to False in package_search, so without it
    # this would always report the public count even for a logged-in user -
    # CKAN's own authorization check still limits results to datasets the
    # acting user (from context) can actually see, so this stays safe for
    # anonymous visitors too.
    context = {"user": toolkit.g.user}
    return toolkit.get_action("package_search")(
        context, {"rows": 0, "include_private": True}
    )["count"]


def harvestportal_organization_count():
    return len(toolkit.get_action("organization_list")({}, {"all_fields": False}))


def harvestportal_group_count():
    return len(toolkit.get_action("group_list")({}, {"all_fields": False}))


def harvestportal_use_sso_login():
    # Defaults to True so an environment that forgets to set this config
    # option falls back to the production SSO flow rather than silently
    # exposing the standard username/password login.
    return toolkit.asbool(
        toolkit.config.get("ckanext.harvestportal.use_sso_login", True)
    )


def get_helpers():
    return {
        "harvestportal_hello": harvestportal_hello,
        "harvestportal_dataset_count": harvestportal_dataset_count,
        "harvestportal_organization_count": harvestportal_organization_count,
        "harvestportal_group_count": harvestportal_group_count,
        "harvestportal_use_sso_login": harvestportal_use_sso_login,
    }
