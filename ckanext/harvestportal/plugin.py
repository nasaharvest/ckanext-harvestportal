import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


# import ckanext.harvestportal.cli as cli
# import ckanext.harvestportal.helpers as helpers
# import ckanext.harvestportal.views as views
# from ckanext.harvestportal.logic import (
#     action, auth, validators
# )


class HarvestportalPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)

    # plugins.implements(plugins.IAuthFunctions)
    # plugins.implements(plugins.IActions)
    # plugins.implements(plugins.IBlueprint)
    # plugins.implements(plugins.IClick)
    # plugins.implements(plugins.ITemplateHelpers)
    # plugins.implements(plugins.IValidators)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "harvestportal")

    def create_resource_schema(self):
        schema = super(HarvestportalPlugin, self).create_resource_schema()
        schema.update(
            {
                "extra_resource_meta": [
                    toolkit.get_validator("ignore_empty"),
                    toolkit.get_validator("json_dict"),
                    toolkit.get_converter("convert_to_extras"),
                ]
            }
        )
        return schema

    def update_resource_schema(self):
        schema = super(HarvestportalPlugin, self).update_resource_schema()
        schema.update(
            {
                "extra_resource_meta": [
                    toolkit.get_validator("ignore_empty"),
                    toolkit.get_validator("json_dict"),
                    toolkit.get_converter("convert_to_extras"),
                ]
            }
        )
        return schema

    def show_resource_schema(self):
        schema = super(HarvestportalPlugin, self).show_resource_schema()
        schema.update(
            {
                "extra_resource_meta": [
                    toolkit.get_validator("ignore_empty"),
                    toolkit.get_validator("json_dict"),
                    toolkit.get_converter("convert_to_extras"),
                ]
            }
        )
        return schema

    # IAuthFunctions

    # def get_auth_functions(self):
    #     return auth.get_auth_functions()

    # IActions

    # def get_actions(self):
    #     return action.get_actions()

    # IBlueprint

    # def get_blueprint(self):
    #     return views.get_blueprints()

    # IClick

    # def get_commands(self):
    #     return cli.get_commands()

    # ITemplateHelpers

    # def get_helpers(self):
    #     return helpers.get_helpers()

    # IValidators

    # def get_validators(self):
    #     return validators.get_validators()
