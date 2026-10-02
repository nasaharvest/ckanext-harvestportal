from flask import request

import ckan.plugins.toolkit as toolkit


def init_cors_max_age(app):
    # Browser dashboards calling the API from another site send a CORS
    # preflight (OPTIONS) before nearly every call, because CKAN never sets
    # Access-Control-Max-Age and browsers then only remember the answer for
    # about 5 seconds. Letting them cache it removes ~40-50% of those
    # dashboards' requests. It caches only the permission check, never data,
    # and is ignored by browsers whenever CKAN doesn't allow the origin.
    max_age = toolkit.asint(
        toolkit.config.get("ckanext.harvestportal.cors_max_age", 7200)
    )
    if max_age <= 0:
        return

    @app.after_request
    def cache_cors_preflight(response):
        if (request.method == "OPTIONS"
                and "Access-Control-Request-Method" in request.headers):
            response.headers["Access-Control-Max-Age"] = str(max_age)
        return response
