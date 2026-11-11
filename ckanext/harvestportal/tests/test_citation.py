"""Tests for dataset citations (citation.py, the Cite dialog, downloads)."""

import datetime
import json

import pytest

import ckan.tests.factories as factories

from ckanext.harvestportal import citation

TODAY = datetime.date(2026, 11, 11)
URL = "https://data.example/dataset/field-boundaries"


def _data(**dataset):
    base = {
        "name": "field-boundaries",
        "title": "CONUS Field Boundaries 2010",
        "author": "",
        "organization": {"title": "Michigan State University"},
        "metadata_created": "2026-02-04T16:59:18.123456",
        "version": "",
        "url": "",
        "extras": [],
    }
    base.update(dataset)
    return citation.citation_data(base, "Harvest Portal", URL, today=TODAY)


def _styles(d):
    return {key: text for key, _label, _html, text in citation.formatted_citations(d)}


# --- author parsing ---------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("Ritvik Sahajpal", [("Ritvik", "Sahajpal")]),
    ("Sahajpal, Ritvik", [("Ritvik", "Sahajpal")]),
    ("Smith, J. A.", [("J. A.", "Smith")]),
    ("Yuval Sadeh, Vasu Thakur", [("Yuval", "Sadeh"), ("Vasu", "Thakur")]),
    ("A B; C D and E F", [("A", "B"), ("C", "D"), ("E", "F")]),
    ("Hannah Ritchie & Max Roser", [("Hannah", "Ritchie"), ("Max", "Roser")]),
    ("OECD", ["OECD"]),
    ("OECD, FAO", ["OECD", "FAO"]),
    ("", []),
])
def test_parse_authors(text, expected):
    got = [n.literal if n.is_group else (n.given, n.family)
           for n in citation.parse_authors(text)]
    assert got == expected


# --- metadata rules ---------------------------------------------------------

def test_organization_is_group_author_when_no_author():
    d = _data()
    assert d["authors"][0].literal == "Michigan State University"


def test_portal_is_author_when_no_author_or_organization():
    d = _data(organization=None)
    assert d["authors"][0].literal == "Harvest Portal"


@pytest.mark.parametrize("version,kept", [
    ("1.2", "1.2"), ("v3", "v3"), ("2.0.1", "2.0.1"),
    ("2021", ""), ("2020-2029", ""), ("December 16, 2020-October 04, 2021", ""),
])
def test_version_only_when_it_looks_like_one(version, kept):
    assert _data(version=version)["version"] == kept


def test_publication_date_extra_and_created_fallback():
    assert _data()["published"] == (2026, 2, 4)
    d = _data(extras=[{"key": "Publication Date", "value": "December, 2023 "}])
    assert d["published"] == (2023, 12, None)


def test_doi_from_extra_or_doi_url():
    d = _data(extras=[{"key": "DOI", "value": "doi:10.5281/zenodo.123456"}])
    assert d["doi"] == "10.5281/zenodo.123456"
    assert d["url"] == "https://doi.org/10.5281/zenodo.123456"
    d = _data(url="https://doi.org/10.1000/xyz.2.")
    assert d["doi"] == "10.1000/xyz.2"
    assert _data(url="https://example.com/10.1000/abc")["doi"] == ""


def test_provider_citation_extra():
    d = _data(extras=[{"key": "Citation ", "value": "FAO/NASA Harvest 2021"}])
    assert d["provider_citation"] == "FAO/NASA Harvest 2021"


# --- styles -----------------------------------------------------------------

def test_styles_group_author():
    s = _styles(_data())
    assert s["apa"] == ("Michigan State University. (2026). CONUS Field Boundaries 2010 "
                        "[Data set]. Harvest Portal. " + URL)
    assert s["mla"] == ("Michigan State University. CONUS Field Boundaries 2010. Harvest "
                        "Portal, 4 Feb. 2026, data.example/dataset/field-boundaries. "
                        "Accessed 11 Nov. 2026.")
    assert s["chicago"].startswith("Michigan State University. CONUS Field Boundaries 2010. "
                                   "Harvest Portal, 2026. Dataset.")
    assert s["harvard"].endswith("(Accessed: 11 November 2026).")
    assert "[cited 2026 Nov 11]" in s["vancouver"]
    assert s["ieee"].startswith("Michigan State University, “CONUS Field Boundaries 2010,”")


def test_styles_people_version_doi():
    d = _data(author="Yuval Sadeh, Vasu Thakur; Ritvik Sahajpal", version="1.2",
              extras=[{"key": "doi", "value": "10.5281/zenodo.123456"}])
    s = _styles(d)
    assert s["apa"].startswith("Sadeh, Y., Thakur, V., & Sahajpal, R. (2026). "
                               "CONUS Field Boundaries 2010 (Version 1.2) [Data set].")
    assert s["apa"].endswith("https://doi.org/10.5281/zenodo.123456")
    assert s["mla"].startswith("Sadeh, Yuval, et al.")
    assert s["chicago"].startswith("Sadeh, Yuval, Vasu Thakur, and Ritvik Sahajpal.")
    assert s["harvard"].startswith("Sadeh, Y., Thakur, V. and Sahajpal, R. (2026)")
    assert s["vancouver"].startswith("Sadeh Y, Thakur V, Sahajpal R.")
    assert s["ieee"].startswith("Y. Sadeh, V. Thakur, and R. Sahajpal,")


def test_two_authors_mla_and_chicago():
    s = _styles(_data(author="Hannah Ritchie & Max Roser"))
    assert s["mla"].startswith("Ritchie, Hannah, and Max Roser.")
    assert s["chicago"].startswith("Ritchie, Hannah, and Max Roser.")
    assert s["ieee"].startswith("H. Ritchie and M. Roser,")


def test_html_italicises_title_and_escapes():
    d = _data(title='Crops <b>& "Fields"')
    html = {k: h for k, _l, h, _t in citation.formatted_citations(d)}
    assert "<i>Crops &lt;b&gt;&amp; &#34;Fields&#34;</i>" in str(html["apa"])
    assert "<b>" not in str(html["apa"])


def test_author_field_can_be_ignored():
    d = citation.citation_data(
        {"name": "x", "title": "Yield Data", "author": "Blake Munshell",
         "organization": {"name": "fao", "title": "FAO"}, "extras": []},
        "Portal", URL, today=TODAY, use_author_field=False)
    assert [n.literal for n in d["authors"]] == ["FAO"]
    assert d["author_source"] == "organization"


def test_filing_organization_is_not_an_author():
    d = citation.citation_data(
        {"name": "x", "title": "Global School Closures", "author": "",
         "organization": {"name": "external-sources", "title": "External Sources"},
         "metadata_created": "2022-03-01T00:00:00", "extras": []},
        "Harvest Portal", URL, today=TODAY, non_author_orgs=["external-sources"])
    assert d["authors"] == []
    assert d["author_source"] == "none"
    s = _styles(d)
    assert s["apa"] == "Global School Closures [Data set]. (2022). Harvest Portal. " + URL
    assert s["mla"].startswith("Global School Closures. Harvest Portal, 1 Mar. 2022,")
    assert s["chicago"].startswith("Global School Closures. Harvest Portal, 2022. Dataset.")
    assert s["harvard"].startswith("Global School Closures (2022) [Data set]. Harvest Portal.")
    assert s["vancouver"].startswith("Global School Closures [dataset on the Internet]. Harvest Portal; 2022")
    assert s["ieee"].startswith("\u201cGlobal School Closures,\u201d Harvest Portal, 2022.")
    assert "External Sources" not in " ".join(s.values())
    bib = citation.to_bibtex(d)
    assert bib.startswith("@misc{dataset2022global,") and "author =" not in bib
    assert "AU  -" not in citation.to_ris(d)
    assert "author" not in json.loads(citation.to_csl_json(d))[0]


def test_listed_author_still_used_under_a_filing_organization():
    d = citation.citation_data(
        {"name": "x", "title": "T", "author": "Our World in Data",
         "organization": {"name": "external-sources", "title": "External Sources"}, "extras": []},
        "Harvest Portal", URL, today=TODAY, non_author_orgs=["external-sources"])
    assert d["author_source"] == "author"


# --- files ------------------------------------------------------------------

def test_bibtex():
    bib = citation.to_bibtex(_data(author="Sahajpal, Ritvik", title="Yield & 50% {test}"))
    assert bib.startswith("@misc{sahajpal2026yield,")
    assert "author = {Sahajpal, Ritvik}" in bib
    assert r"title = {{Yield \& 50\% \{test\}}}" in bib
    assert "year = {2026}" in bib
    bib = citation.to_bibtex(_data())
    assert "author = {{Michigan State University}}" in bib


def test_ris():
    ris = citation.to_ris(_data(author="Ritvik Sahajpal"))
    lines = ris.split("\r\n")
    assert lines[0] == "TY  - DATA"
    assert "AU  - Sahajpal, Ritvik" in lines
    assert "PY  - 2026" in lines
    assert "UR  - " + URL in lines
    assert lines[-2] == "ER  - "


def test_csl_json():
    item = json.loads(citation.to_csl_json(_data()))[0]
    assert item["type"] == "dataset"
    assert item["author"] == [{"literal": "Michigan State University"}]
    assert item["issued"] == {"date-parts": [[2026, 2, 4]]}


# --- CKAN integration -------------------------------------------------------

@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_dataset_page_has_cite_dialog(app):
    org = factories.Organization(title="Partner University")
    dataset = factories.Dataset(owner_org=org["id"], title="Soil <script>x</script> moisture")

    body = app.get("/dataset/{}".format(dataset["name"])).body

    assert 'data-bs-target="#cite-dialog"' in body
    assert "Cite this dataset" in body
    assert "The organization that published this dataset is cited as the author." in body
    assert "Partner University. (" in body
    assert "<script>x</script>" not in body
    assert "/dataset/{}/citation.bib".format(dataset["name"]) in body


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
@pytest.mark.parametrize("fmt,content_type,start", [
    ("bib", "application/x-bibtex", "@misc{"),
    ("ris", "application/x-research-info-systems", "TY  - DATA"),
    ("json", "application/vnd.citationstyles.csl+json", "["),
])
def test_citation_downloads(app, fmt, content_type, start):
    dataset = factories.Dataset(owner_org=factories.Organization()["id"])

    resp = app.get("/dataset/{}/citation.{}".format(dataset["name"], fmt))

    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith(content_type)
    assert resp.headers["Content-Disposition"] == \
        'attachment; filename="{}.{}"'.format(dataset["name"], fmt)
    assert resp.body.startswith(start)


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_citation_download_private_and_missing(app):
    org = factories.Organization()
    private = factories.Dataset(owner_org=org["id"], private=True)

    assert app.get("/dataset/{}/citation.bib".format(private["name"])).status_code in (403, 404)
    assert app.get("/dataset/no-such-dataset/citation.bib").status_code == 404
    assert app.get("/dataset/{}/citation.exe".format(private["name"])).status_code == 404


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_harvest_defaults_ignore_author_and_external_sources(app):
    fao = factories.Organization(name="fao-test", title="FAO")
    ext = factories.Organization(name="external-sources", title="External Sources")
    by_fao = factories.Dataset(owner_org=fao["id"], author="Blake Munshell", title="Malawi labels")
    by_ext = factories.Dataset(owner_org=ext["id"], author="", title="School closures")

    bib = app.get("/dataset/{}/citation.bib".format(by_fao["name"])).body
    assert "author = {{FAO}}" in bib and "Munshell" not in bib
    body = app.get("/dataset/{}".format(by_ext["name"])).body
    assert "External Sources. (" not in body
    assert "This dataset does not name an author" in body


@pytest.mark.ckan_config("ckan.plugins", "harvestportal")
@pytest.mark.ckan_config("ckanext.harvestportal.citation.use_author_field", "true")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_harvest_author_field_can_be_switched_on(app):
    org = factories.Organization(title="FAO")
    ds = factories.Dataset(owner_org=org["id"], author="Blake Munshell")
    bib = app.get("/dataset/{}/citation.bib".format(ds["name"])).body
    assert "author = {Munshell, Blake}" in bib
