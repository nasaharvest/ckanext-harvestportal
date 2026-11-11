from flask import Blueprint

import ckan.plugins.toolkit as toolkit

from ckanext.harvestportal import citation


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


def citation_file(id, fmt):
    """Download a dataset citation as BibTeX, RIS or CSL-JSON.

    Uses package_show with the visitor's own permissions, so private
    datasets stay private (404/403 like the dataset page).
    """
    context = {"user": toolkit.current_user.name if toolkit.current_user else ""}
    try:
        dataset = toolkit.get_action("package_show")(context, {"id": id})
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, toolkit._("Dataset not found"))
    except toolkit.NotAuthorized:
        return toolkit.abort(403, toolkit._("Not authorized to see this dataset"))
    data = citation_data_for(dataset)
    _label, content_type = citation.FILE_FORMATS[fmt]
    body = citation.FILE_BUILDERS[fmt](data)
    filename = "{}.{}".format(dataset["name"], fmt)
    return body, 200, {
        "Content-Type": content_type,
        "Content-Disposition": 'attachment; filename="{}"'.format(filename),
    }


def citation_data_for(dataset):
    return citation.citation_data(
        dataset,
        site_title=toolkit.config.get("ckan.site_title") or "Harvest Portal",
        dataset_url=toolkit.url_for("dataset.read", id=dataset["name"], _external=True),
    )


harvestportal.add_url_rule(
    "/dataset/<id>/citation.<any(bib, ris, json):fmt>", view_func=citation_file
)


def get_blueprints():
    return [harvestportal]
