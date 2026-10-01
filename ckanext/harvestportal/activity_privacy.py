"""Hide who made an edit from anonymous visitors (activity plugin).

With ckan.auth.public_user_details = false, anonymous visitors can't see user
profiles, but the activity plugin's streams would still show each editor's
full name on public datasets, and its API would return their user id and
username. This keeps the two consistent: anonymous visitors see what changed
and when, not who changed it. Logged-in users and sysadmins are unaffected,
and nothing changes if public_user_details is true.
"""

import ckan.authz as authz
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

ACTIVITY_ACTIONS = [
    "package_activity_list",
    "organization_activity_list",
    "group_activity_list",
    "recently_changed_packages_activity_list",
    "user_activity_list",
    "activity_show",
]


def _hide_users():
    # Read the same way CKAN's own user auth functions read it (it isn't one
    # of authz.check_config_permission's keys).
    return not toolkit.asbool(
        toolkit.config.get("ckan.auth.public_user_details"))


def anonymous_actor_label():
    return toolkit._("A Harvest Portal user")


@toolkit.chained_helper
def linked_user(next_helper, user, maxlength=0, avatar=20):
    # Activity templates (and the few core templates an anonymous visitor
    # can reach) render the editor through this helper.
    if _hide_users() and toolkit.current_user.is_anonymous:
        return anonymous_actor_label()
    return next_helper(user, maxlength, avatar)


def _strip_actor(activity):
    activity["user_id"] = None
    if isinstance(activity.get("data"), dict) and "actor" in activity["data"]:
        activity["data"]["actor"] = None
    return activity


def _chain(name):
    @toolkit.chained_action
    @toolkit.side_effect_free
    def action(original_action, context, data_dict):
        result = original_action(context, data_dict)
        if _hide_users() and authz.auth_is_anon_user(context):
            if isinstance(result, list):
                result = [_strip_actor(a) for a in result]
            elif isinstance(result, dict):
                result = _strip_actor(result)
        return result

    action.__name__ = name
    return action


def get_actions():
    # Chaining an action that doesn't exist fails at startup, so only do it
    # when the activity plugin is enabled.
    if not plugins.plugin_loaded("activity"):
        return {}
    return {name: _chain(name) for name in ACTIVITY_ACTIONS}
