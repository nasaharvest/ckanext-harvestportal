from flask import Blueprint

import ckan.plugins.toolkit as toolkit


harvestportal = Blueprint(
    "harvestportal", __name__)


def page():
    return "Hello, harvestportal!"


def health():
    # Load balancer health check. Deliberately does no DB/Solr work so a busy
    # but working task isn't marked unhealthy and replaced mid-traffic spike.
    return "OK", 200, {"Content-Type": "text/plain"}


def api_docs():
    return toolkit.render("api_docs.html")


def api_examples():
    return toolkit.render("api_examples.html")


def mcp_docs():
    return toolkit.render("mcp_docs.html")


harvestportal.add_url_rule(
    "/harvestportal/page", view_func=page)
harvestportal.add_url_rule(
    "/health", view_func=health)
harvestportal.add_url_rule(
    "/api-docs", view_func=api_docs)
harvestportal.add_url_rule(
    "/api-examples", view_func=api_examples)
harvestportal.add_url_rule(
    "/mcp-docs", view_func=mcp_docs)


def get_blueprints():
    return [harvestportal]
