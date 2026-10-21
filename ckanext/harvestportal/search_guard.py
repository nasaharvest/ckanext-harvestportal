import re

from flask import request

import ckan.plugins.toolkit as toolkit


TOO_MANY_FILTERS_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="robots" content="noindex, nofollow">
<title>Too many filters - Harvest Portal</title></head>
<body style="font-family: sans-serif; max-width: 40em; margin: 4em auto; padding: 0 1em">
<h1>Too many search filters</h1>
<p>This search combines more filters than we support. Please remove some
filters and try again.</p>
<p><a href="/dataset/">Start a new dataset search</a></p>
</body></html>"""


def _filter_count(args):
    # Same rule as CKAN's dataset search view uses to turn query parameters
    # into Solr filters.
    return sum(
        1
        for key, value in args.items(multi=True)
        if value
        and key not in ("q", "page", "sort")
        and not key.startswith(("_", "ext_"))
    )


# Pages that run a faceted dataset search: the search page, and the dataset
# lists on organization and group pages.
GUARDED_ENDPOINTS = frozenset({"dataset.search", "organization.read", "group.read"})


SHOW_MORE_PARAM = re.compile(r"_\w+_limit")


def _has_show_more(args):
    # "Show more <facet>" links add _<facet>_limit=0.
    return any(SHOW_MORE_PARAM.fullmatch(key) for key in args)


def init_search_guard(app):
    # A residential-proxy botnet walks every facet combination of the search
    # page and of organization/group pages; nearly all its requests carry 4+
    # filter values, or a "Show more" parameter on top of 3+ filters, which
    # real users almost never do. Refusing those before running the search
    # costs ~1 ms instead of a Solr query and a full page render. A plain
    # "Show more" click with 0-2 filters selected still works.
    max_filters = toolkit.asint(
        toolkit.config.get("ckanext.harvestportal.search_max_filters", 3)
    )
    show_more_max_filters = toolkit.asint(
        toolkit.config.get("ckanext.harvestportal.show_more_max_filters", 2)
    )

    @app.before_request
    def refuse_deep_facet_searches():
        if request.endpoint not in GUARDED_ENDPOINTS:
            return None
        filters = _filter_count(request.args)
        limit = show_more_max_filters if _has_show_more(request.args) else max_filters
        if filters <= limit:
            return None
        return TOO_MANY_FILTERS_PAGE, 400, {"Content-Type": "text/html; charset=utf-8"}

    return app
