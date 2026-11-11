"""Dataset citations: formatted styles and reference-manager files.

Shared by the NASA Acres Portal (ckanext-acresportal) and the Harvest Portal
(ckanext-harvestportal); keep the two copies identical. Pure Python, no CKAN
imports, so it can be tested on its own.

Builds, from a CKAN dataset dict:
  - APA 7, MLA 9, Chicago (17th, bibliography), Harvard, Vancouver and IEEE
    citations, each as HTML (titles in italics) and plain text;
  - BibTeX, RIS and CSL-JSON files.

Metadata rules (most datasets only have some of these fields):
  - authors: the dataset's "author" field; if empty, the organization is
    cited as a group author; failing that, the portal itself.
  - year: a "Publication Date" extra if it contains a year, otherwise the
    year the dataset was created on the portal.
  - version: only when it looks like a version number (v2, 1.0.3); on the
    Harvest Portal the field often holds years or date ranges instead.
  - DOI: a "doi" extra, or a doi.org link in the dataset's source URL.
  - publisher: the portal (the repository that hosts the dataset).
"""

import datetime
import json
import re

from markupsafe import Markup, escape

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
MLA_MONTHS = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "June", "July", "Aug.",
              "Sept.", "Oct.", "Nov.", "Dec."]
SHORT_MONTHS = [m[:3] for m in MONTHS]

STYLES = [
    ("apa", "APA"),
    ("mla", "MLA"),
    ("chicago", "Chicago"),
    ("harvard", "Harvard"),
    ("vancouver", "Vancouver"),
    ("ieee", "IEEE"),
]

FILE_FORMATS = {
    # extension: (label, content type)
    "bib": ("BibTeX", "application/x-bibtex; charset=utf-8"),
    "ris": ("RIS", "application/x-research-info-systems; charset=utf-8"),
    "json": ("CSL-JSON", "application/vnd.citationstyles.csl+json; charset=utf-8"),
}

DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\"<>]+[^\s\"<>.,;)\]])")
# "1.2", "2.0.1", "v3"; not "2021" or "2020-2029" (years in the version field)
VERSION_RE = re.compile(r"^(v\d+(\.\d+){0,3}|\d+(\.\d+){1,3})[a-z]?$", re.I)
YEAR_RE = re.compile(r"\b(1[89]\d\d|2\d\d\d)\b")
# Keys data providers use for their own preferred citation (compared after
# lower-casing and stripping, e.g. "Citation " on one Harvest dataset).
PROVIDER_CITATION_KEYS = {"citation", "suggested citation", "how to cite",
                          "preferred citation", "recommended citation"}


# ---------------------------------------------------------------------------
# Names

class Name:
    """A person (given/family) or a group author (literal)."""

    def __init__(self, family=None, given=None, literal=None):
        self.family = family
        self.given = given
        self.literal = literal

    @property
    def is_group(self):
        return self.literal is not None

    def initials(self, sep=". ", end="."):
        parts = re.split(r"[\s\-]+", self.given or "")
        letters = [p[0].upper() for p in parts if p]
        return sep.join(letters) + end if letters else ""

    def __repr__(self):
        return "Name({!r})".format(self.literal or (self.given, self.family))


def _person(text):
    """'Ritvik Sahajpal' or 'Sahajpal, Ritvik' -> Name; one word -> group."""
    text = " ".join(text.split())
    if "," in text:
        family, given = [p.strip() for p in text.split(",", 1)]
        if family and given:
            return Name(family=family, given=given)
        text = family or given
    words = text.split(" ")
    if len(words) == 1:
        return Name(literal=text)  # e.g. "OECD"
    return Name(family=words[-1], given=" ".join(words[:-1]))


def parse_authors(text):
    """Parse CKAN's free-text author field into a list of Names.

    Accepts "A B; C D", "A B, C D and E F", "A B & C D" and "Family, Given".
    """
    text = (text or "").strip()
    if not text:
        return []
    parts = re.split(r"\s*;\s*|\s+and\s+|\s*&\s*", text)
    names = []
    for part in parts:
        part = part.strip().strip(",")
        if not part:
            continue
        pieces = [p.strip() for p in part.split(",") if p.strip()]
        if len(pieces) == 2 and " " not in pieces[0] and _looks_like_given(pieces[1]):
            # "Sahajpal, Ritvik" / "Smith, J. A.": one person, family first
            names.append(_person(part))
        else:
            # "Ritvik Sahajpal, Vasu Thakur" or "OECD, FAO": several names
            names.extend(_person(p) for p in pieces)
    return names


def _looks_like_given(text):
    """Given names ("Ritvik", "Mary Ann") or initials ("J. A."), not an
    all-caps acronym ("FAO") or a full name ("Vasu Thakur")."""
    if re.fullmatch(r"([A-Z]\.\s*)+", text):
        return True
    words = text.split()
    return len(words) == 1 and not text.isupper()


# ---------------------------------------------------------------------------
# Metadata

def _extras(dataset):
    return {(e.get("key") or "").strip().lower(): (e.get("value") or "").strip()
            for e in dataset.get("extras") or []}


def _date(value):
    if not value:
        return None
    try:
        return datetime.datetime.fromisoformat(value[:19]).date()
    except ValueError:
        return None


def citation_data(dataset, site_title, dataset_url, today=None):
    """Collect what the citations need from a CKAN dataset dict."""
    extras = _extras(dataset)
    org = (dataset.get("organization") or {}).get("title")
    authors = parse_authors(dataset.get("author"))
    if not authors:
        authors = [Name(literal=org or site_title)]

    created = _date(dataset.get("metadata_created"))
    published = None
    pub_text = extras.get("publication date", "")
    year_match = YEAR_RE.search(pub_text)
    if year_match:
        year = int(year_match.group(1))
        month = next((i + 1 for i, m in enumerate(MONTHS) if m.lower() in pub_text.lower()), None)
        published = (year, month, None)
    elif created:
        published = (created.year, created.month, created.day)

    version = (dataset.get("version") or "").strip()
    if not VERSION_RE.match(version):
        version = ""

    doi = extras.get("doi", "")
    if not DOI_RE.search(doi):
        doi = ""
    if not doi:
        match = DOI_RE.search(dataset.get("url") or "")
        doi = match.group(1) if match and "doi.org" in (dataset.get("url") or "") else ""
    else:
        doi = DOI_RE.search(doi).group(1)

    provider = next((v for k, v in extras.items() if k in PROVIDER_CITATION_KEYS and v), "")

    return {
        "authors": authors,
        "title": (dataset.get("title") or dataset.get("name") or "").strip(),
        "published": published,          # (year, month|None, day|None) or None
        "version": version,
        "publisher": site_title,
        "url": "https://doi.org/" + doi if doi else dataset_url,
        "page_url": dataset_url,
        "doi": doi,
        "accessed": today or datetime.date.today(),
        "provider_citation": provider,
        "name": dataset.get("name") or "",
    }


# ---------------------------------------------------------------------------
# Author lists per style

def _join(items, last_sep, two_sep=None, sep=", "):
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return items[0] + (two_sep if two_sep is not None else last_sep) + items[1]
    return sep.join(items[:-1]) + last_sep + items[-1]


def _apa_authors(names):
    def one(n):
        return n.literal if n.is_group else "{}, {}".format(n.family, n.initials())
    items = [one(n) for n in names]
    if len(items) > 20:
        items = items[:19] + ["... " + items[-1]]
    return _join(items, ", & ", two_sep=", & ")


def _harvard_authors(names):
    def one(n):
        return n.literal if n.is_group else "{}, {}".format(n.family, n.initials(sep=".", end="."))
    return _join([one(n) for n in names], " and ")


def _mla_authors(names):
    first = names[0]
    lead = first.literal if first.is_group else "{}, {}".format(first.family, first.given)
    if len(names) == 1:
        return lead
    if len(names) == 2:
        second = names[1]
        other = second.literal if second.is_group else "{} {}".format(second.given, second.family)
        return "{}, and {}".format(lead, other)
    return lead + ", et al"


def _chicago_authors(names):
    def rest(n):
        return n.literal if n.is_group else "{} {}".format(n.given, n.family)
    first = names[0]
    lead = first.literal if first.is_group else "{}, {}".format(first.family, first.given)
    if len(names) > 10:
        return ", ".join([lead] + [rest(n) for n in names[1:7]]) + ", et al"
    return _join([lead] + [rest(n) for n in names[1:]], ", and ", two_sep=", and ")


def _vancouver_authors(names):
    def one(n):
        return n.literal if n.is_group else "{} {}".format(n.family, n.initials(sep="", end=""))
    items = [one(n) for n in names]
    if len(items) > 6:
        items = items[:6] + ["et al"]
    return ", ".join(items)


def _ieee_authors(names):
    def one(n):
        return n.literal if n.is_group else "{} {}".format(n.initials(), n.family)
    items = [one(n) for n in names]
    if len(items) > 6:
        return items[0] + " et al."
    return _join(items, ", and ", two_sep=" and ")


def _period(text):
    """End a sentence with exactly one period."""
    return text if text.endswith((".", "?", "!")) else text + "."


# ---------------------------------------------------------------------------
# Styles. Each returns a list of parts: plain strings or ("i", text) for
# italics, joined into HTML (escaped) and plain text.

def _apa(d):
    year = d["published"][0] if d["published"] else "n.d."
    title = [("i", d["title"])]
    if d["version"]:
        title.append(" (Version {})".format(d["version"]))
    return [_period(_apa_authors(d["authors"])), " ({}). ".format(year)] + title + \
        [" [Data set]. ", _period(d["publisher"]), " ", d["url"]]


def _mla(d):
    parts = [_period(_mla_authors(d["authors"])), " ", ("i", _period(d["title"])), " "]
    if d["version"]:
        parts.append("Version {}, ".format(d["version"]))
    parts.append(d["publisher"])
    if d["published"]:
        y, m, day = d["published"]
        date = " ".join(str(x) for x in [day, MLA_MONTHS[m - 1] if m else None, y] if x)
        parts.append(", " + date)
    a = d["accessed"]
    parts.append(", {}. Accessed {} {} {}.".format(
        re.sub(r"^https?://", "", d["url"]), a.day, MLA_MONTHS[a.month - 1], a.year))
    return parts


def _chicago(d):
    parts = [_period(_chicago_authors(d["authors"])), " ", ("i", _period(d["title"])), " "]
    if d["version"]:
        parts.append("Version {}. ".format(d["version"]))
    parts.append(d["publisher"])
    if d["published"]:
        parts.append(", {}".format(d["published"][0]))
    parts.append(". Dataset. " + d["url"] + ".")
    return parts


def _harvard(d):
    year = d["published"][0] if d["published"] else "n.d."
    a = d["accessed"]
    parts = [_harvard_authors(d["authors"]), " ({}) ".format(year), ("i", d["title"])]
    if d["version"]:
        parts.append(" (Version {})".format(d["version"]))
    parts.append(" [Data set]. {}. Available at: {} (Accessed: {} {} {}).".format(
        d["publisher"], d["url"], a.day, MONTHS[a.month - 1], a.year))
    return parts


def _vancouver(d):
    a = d["accessed"]
    year = d["published"][0] if d["published"] else ""
    parts = [_period(_vancouver_authors(d["authors"])), " ", d["title"], " [dataset on the Internet]"]
    if d["version"]:
        parts.append(". Version {}".format(d["version"]))
    parts.append(". {}; {} [cited {} {} {}]. Available from: {}".format(
        d["publisher"], year, a.year, SHORT_MONTHS[a.month - 1], a.day, d["url"]))
    return parts


def _ieee(d):
    a = d["accessed"]
    parts = [_ieee_authors(d["authors"]), ", “", d["title"], ",” "]
    if d["version"]:
        parts.append("Version {}, ".format(d["version"]))
    parts.append(d["publisher"])
    if d["published"]:
        parts.append(", {}".format(d["published"][0]))
    parts.append(". [Online]. Available: {} (accessed {} {}, {}).".format(
        d["url"], SHORT_MONTHS[a.month - 1] + ".", a.day, a.year))
    return parts


_STYLE_FUNCS = {"apa": _apa, "mla": _mla, "chicago": _chicago,
                "harvard": _harvard, "vancouver": _vancouver, "ieee": _ieee}


def _render(parts):
    html, text = Markup(""), ""
    for part in parts:
        if isinstance(part, tuple):
            html += Markup("<i>{}</i>").format(part[1])
            text += part[1]
        else:
            html += escape(part)
            text += part
    return html, text


def formatted_citations(d):
    """[(key, label, html, text)] for every style."""
    out = []
    for key, label in STYLES:
        html, text = _render(_STYLE_FUNCS[key](d))
        out.append((key, label, html, text))
    return out


# ---------------------------------------------------------------------------
# Reference-manager files

def _bibtex_escape(text):
    text = text.replace("\\", r"\textbackslash{}")
    for ch in "&%$#_{}":
        text = text.replace(ch, "\\" + ch)
    return text.replace("~", r"\textasciitilde{}").replace("^", r"\textasciicircum{}")


def bibtex_key(d):
    first = d["authors"][0]
    who = first.literal if first.is_group else first.family
    who = re.sub(r"[^a-z0-9]", "", who.lower())[:20] or "dataset"
    year = d["published"][0] if d["published"] else ""
    word = next((w for w in re.findall(r"[a-z0-9]+", d["title"].lower())
                 if w not in {"a", "an", "the", "of", "and", "for", "in", "on"}), "")
    return "{}{}{}".format(who, year, word)


def to_bibtex(d):
    def author(n):
        return "{" + _bibtex_escape(n.literal) + "}" if n.is_group \
            else "{}, {}".format(_bibtex_escape(n.family), _bibtex_escape(n.given))
    fields = [
        ("author", " and ".join(author(n) for n in d["authors"])),
        ("title", "{" + _bibtex_escape(d["title"]) + "}"),
        ("year", str(d["published"][0]) if d["published"] else ""),
        ("publisher", _bibtex_escape(d["publisher"])),
        ("version", _bibtex_escape(d["version"])),
        ("doi", d["doi"]),
        ("url", d["url"]),
        ("howpublished", "\\url{" + d["url"] + "}"),
        ("note", "Dataset. Accessed {}".format(d["accessed"].isoformat())),
    ]
    body = ",\n".join("  {} = {{{}}}".format(k, v) for k, v in fields if v)
    return "@misc{{{},\n{}\n}}\n".format(bibtex_key(d), body)


def to_ris(d):
    lines = ["TY  - DATA"]
    for n in d["authors"]:
        lines.append("AU  - " + (n.literal if n.is_group else "{}, {}".format(n.family, n.given)))
    lines.append("TI  - " + d["title"])
    if d["published"]:
        y, m, day = d["published"]
        lines.append("PY  - {}".format(y))
        lines.append("DA  - {}/{}/{}/".format(y, "%02d" % m if m else "", "%02d" % day if day else ""))
    lines.append("PB  - " + d["publisher"])
    if d["version"]:
        lines.append("ET  - " + d["version"])
    if d["doi"]:
        lines.append("DO  - " + d["doi"])
    lines.append("UR  - " + d["url"])
    lines.append("Y2  - " + d["accessed"].strftime("%Y/%m/%d"))
    lines.append("ER  - ")
    return "\r\n".join(lines) + "\r\n"


def to_csl_json(d):
    def author(n):
        return {"literal": n.literal} if n.is_group else {"family": n.family, "given": n.given}
    item = {
        "id": bibtex_key(d),
        "type": "dataset",
        "title": d["title"],
        "author": [author(n) for n in d["authors"]],
        "publisher": d["publisher"],
        "URL": d["url"],
        "accessed": {"date-parts": [[d["accessed"].year, d["accessed"].month, d["accessed"].day]]},
    }
    if d["published"]:
        item["issued"] = {"date-parts": [[x for x in d["published"] if x]]}
    if d["version"]:
        item["version"] = d["version"]
    if d["doi"]:
        item["DOI"] = d["doi"]
    return json.dumps([item], indent=2, ensure_ascii=False) + "\n"


FILE_BUILDERS = {"bib": to_bibtex, "ris": to_ris, "json": to_csl_json}
