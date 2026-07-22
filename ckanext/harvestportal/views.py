from flask import Blueprint

import ckan.plugins.toolkit as toolkit


harvestportal = Blueprint(
    "harvestportal", __name__)


def page():
    return "Hello, harvestportal!"


def api_docs():
    return toolkit.render("api_docs.html")


harvestportal.add_url_rule(
    "/harvestportal/page", view_func=page)
harvestportal.add_url_rule(
    "/api-docs", view_func=api_docs)


def get_blueprints():
    return [harvestportal]
