from flask import request
from werkzeug.wrappers import Response

import ckan.plugins.toolkit as toolkit

DUMP_ENDPOINT = "datastore.dump"

SIGN_IN_REQUIRED = (
    "Sign in to download data exports from the Harvest Portal.\n"
    "Scripts can send a CKAN API token in the Authorization header, or use\n"
    "the DataStore API (datastore_search) without signing in.\n"
)


def exports_require_login():
    return toolkit.asbool(
        toolkit.config.get("ckanext.harvestportal.require_login_for_exports", True)
    )


def init_export_guard(app):
    # Crawlers re-download every table in every export format daily, from
    # thousands of IPs and ignoring robots.txt. Exports (/datastore/dump/,
    # the CSV/TSV/JSON/XML download menu) now need a signed-in user or an
    # API token. Previews, the DataStore API and original uploaded files
    # are unaffected. Browsers go to CKAN's login page (not straight to
    # single sign-on, so crawler hits never reach Cognito); its SSO button
    # passes came_from on, so users land back on their download.
    if not exports_require_login():
        return

    @app.before_request
    def require_login_for_exports():
        if request.endpoint != DUMP_ENDPOINT:
            return None
        if not toolkit.current_user.is_anonymous:
            return None
        # Browsers ask for text/html explicitly; scripts (curl's "*/*")
        # get a plain 401 explaining how to authenticate.
        if "text/html" in request.headers.get("Accept", ""):
            came_from = request.full_path.rstrip("?")
            return toolkit.redirect_to(
                toolkit.url_for("user.login", came_from=came_from))
        return Response(SIGN_IN_REQUIRED, status=401, mimetype="text/plain",
                        headers={"Cache-Control": "no-store"})

