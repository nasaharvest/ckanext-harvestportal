import ckan.plugins.toolkit as tk
import ckanext.harvestportal.logic.schema as schema


@tk.side_effect_free
def harvestportal_get_sum(context, data_dict):
    tk.check_access(
        "harvestportal_get_sum", context, data_dict)
    data, errors = tk.navl_validate(
        data_dict, schema.harvestportal_get_sum(), context)

    if errors:
        raise tk.ValidationError(errors)

    return {
        "left": data["left"],
        "right": data["right"],
        "sum": data["left"] + data["right"]
    }


def get_actions():
    return {
        'harvestportal_get_sum': harvestportal_get_sum,
    }
