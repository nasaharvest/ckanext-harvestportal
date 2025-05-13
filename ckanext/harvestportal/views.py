from flask import Blueprint


harvestportal = Blueprint(
    "harvestportal", __name__)


def page():
    return "Hello, harvestportal!"


harvestportal.add_url_rule(
    "/harvestportal/page", view_func=page)


def get_blueprints():
    return [harvestportal]
