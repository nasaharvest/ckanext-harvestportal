import ckan.plugins.toolkit as tk


@tk.auth_allow_anonymous_access
def harvestportal_get_sum(context, data_dict):
    return {"success": True}


def get_auth_functions():
    return {
        "harvestportal_get_sum": harvestportal_get_sum,
    }
