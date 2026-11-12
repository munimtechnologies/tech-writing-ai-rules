#!/usr/bin/env python3
# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""hugo_layout_check: find Hugo page layouts with no Markdown template.

A Hugo site that adds a Markdown output format (for llms.txt, `<page>.md`
addresses or `Accept: text/markdown`) renders every page twice: once with its
HTML template and once with a Markdown template. When a page names a custom
layout (`layout: glossary`) and the project has `glossary.html` but no
`glossary.markdown.md`, Hugo renders the Markdown copy with the generic
template instead (`single.markdown.md`, `list.markdown.md` and the like). That
template usually prints the title and the page body, so anything the HTML
layout builds from data files, front matter lists or child pages is missing
from the copy, and nothing fails.

This script reads a Hugo project's `layouts/` folder and the layout settings
in its content front matter, content adapters and config files, and reports
each custom layout that has an HTML template but no Markdown template:

  error    layout-loses-content  the HTML template builds content the page
                                 body does not hold (site data, child pages,
                                 or a range over front matter values)
  warning  layout-no-markdown    used by pages, but no such sign was found
  info     unused-layout         no page or config we read uses it
  info     no-markdown-output    the project has no Markdown templates at all

It reads files only: no build, no network. Python standard library only.
Every finding is a sign to check, not proof: compare one page's Markdown copy
with the page.

    python hugo_layout_check.py path/to/hugo-site
    python hugo_layout_check.py path/to/hugo-site --json
    python hugo_layout_check.py site --layouts site/layouts --layouts themes/x/layouts
"""

import argparse
import json
import os
import re
import sys

VERSION = "0.1.0"

SEVERITY = {
    "layout-loses-content": "error",
    "layout-no-markdown": "warning",
    "unused-layout": "info",
    "no-markdown-output": "info",
}

KINDS = {"home", "page", "section", "taxonomy", "term"}
STANDARD = {"single", "list", "all", "baseof", "index", "terms", "404",
            "sitemap", "sitemapindex", "robots"}
KNOWN_FORMATS = {"html", "markdown", "rss", "json", "amp", "calendar", "css",
                 "csv", "robots", "sitemap", "sitemapindex", "llms", "llmsfull",
                 "webappmanifest"}
SKIP_DIRS = {"_partials", "partials", "_shortcodes", "shortcodes", "_markup"}
PREFIXED = re.compile(r"^_(kind|layout|outputformat|language|role|version)_(.+)_$")
LANG = re.compile(r"^[a-z]{2}(?:-[a-z0-9]{2,4})?$")

CONTENT_EXT = {".md", ".markdown", ".mdx", ".html", ".htm", ".adoc", ".asciidoc",
               ".org", ".pandoc", ".rst"}
CONFIG_NAME = re.compile(r"^(?:hugo|config)\.(?:ya?ml|toml|json)$")
CONFIG_EXT = {".yaml", ".yml", ".toml", ".json"}

LAYOUT_YAML = re.compile(r"""^[ \t]*layout[ \t]*:[ \t]*["']?([A-Za-z0-9_-]+)["']?[ \t]*(?:#.*)?$""", re.M)
LAYOUT_TOML = re.compile(r"""^[ \t]*layout[ \t]*=[ \t]*["']([A-Za-z0-9_-]+)["']""", re.M)
LAYOUT_JSON = re.compile(r""""layout"\s*:\s*"([A-Za-z0-9_-]+)\"""")
LAYOUT_GOTMPL = re.compile(r""""layout"\s+"([A-Za-z0-9_-]+)\"""")
CASCADE_YAML = re.compile(r"^[ \t]*-?[ \t]*cascade[ \t]*:", re.M)
CASCADE_TOML = re.compile(r"^[ \t]*\[\[?[ \t]*cascade\b|^[ \t]*cascade[ \t]*=", re.M)

DATA_RE = re.compile(r"\b(?:hugo|site|Site)\.Data\b")
CHILD_RE = re.compile(r"\brange\b[^}]*?\.(?:Pages|RegularPages|RegularPagesRecursive|Sections)\b")
PARAMS_LIST_RE = re.compile(r"\brange\b[^}]*?\.Params\.")
PARAMS_RE = re.compile(r"\.Params\.\w+")
SUMMARY_RE = re.compile(r"\.(?:Summary|Description)\b")
CONTENT_RE = re.compile(r"\.Content\b")
PARTIAL_RE = re.compile(r"""\bpartial(?:Cached)?\s+"([^"]+)\"""")


class UsageError(Exception):
    pass


def norm(path):
    return path.replace(os.sep, "/")


def parse_template(relpath, md_format="markdown", md_suffix="md", languages=None):
    """Read the identifiers in a template's file name.

    Returns a dict with kind, standard, layout, format, language and suffix,
    or None for a name Hugo would not treat as a template.
    """
    name = os.path.basename(relpath)
    parts = name.split(".")
    if len(parts) < 2 or not parts[0]:
        return None
    suffix = parts[-1].lower()
    info = {"path": norm(relpath), "dir": norm(os.path.dirname(relpath)), "suffix": suffix,
            "kind": None, "standard": None, "layout": None, "format": None,
            "language": None}
    unknown = []
    for ident in parts[:-1]:
        m = PREFIXED.match(ident)
        if m:
            key, val = m.group(1), m.group(2)
            if key == "kind":
                info["kind"] = val.lower()
            elif key == "layout":
                info["layout"] = val
            elif key == "outputformat":
                info["format"] = val.lower()
            elif key == "language":
                info["language"] = val.lower()
            continue
        low = ident.lower()
        if low in KINDS and info["kind"] is None:
            info["kind"] = low
        elif low in STANDARD and info["standard"] is None:
            info["standard"] = low
        elif (low in KNOWN_FORMATS or low == md_format) and info["format"] is None:
            info["format"] = low
        elif info["language"] is None and (
                (languages is not None and low in languages)
                or (languages is None and LANG.match(low))):
            info["language"] = low
        else:
            unknown.append(ident)
    if info["format"] is None:
        if suffix in ("html", "htm"):
            info["format"] = "html"
        elif suffix == md_suffix:
            info["format"] = md_format
        elif unknown:
            # home.metadata.json: an unknown name before a non-HTML suffix is
            # a custom output format, not a layout.
            info["format"] = unknown.pop().lower()
        else:
            info["format"] = suffix
    if info["layout"] is None and unknown:
        info["layout"] = unknown[0]
    return info


def collect_templates(layout_dirs, md_format="markdown", md_suffix="md", languages=None):
    out = []
    for base in layout_dirs:
        for root, dirs, files in os.walk(base):
            dirs[:] = sorted(d for d in dirs
                             if d not in SKIP_DIRS and not (d.startswith("_") and d != "_default"))
            for f in sorted(files):
                if f.startswith("_") or f.startswith("."):
                    continue
                full = os.path.join(root, f)
                t = parse_template(os.path.relpath(full, base), md_format, md_suffix, languages)
                if t is not None:
                    t["file"] = full
                    t["base"] = base
                    out.append(t)
    return out


def read_text(path, limit=None):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read(limit) if limit else fh.read()
    except OSError:
        return ""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def front_matter(text):
    """Return (front matter text, format) for a content file, or ("", None)."""
    t = text.lstrip("﻿")
    lines = t.split("\n")
    if lines and lines[0].strip() in ("---", "+++"):
        fence = lines[0].strip()
        for i in range(1, len(lines)):
            if lines[i].strip() == fence:
                return "\n".join(lines[1:i]), ("yaml" if fence == "---" else "toml")
        return "", None
    if t.startswith("{"):
        depth = 0
        for i, ch in enumerate(t):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return t[:i + 1], "json"
        return "", None
    return "", None


def _uses_in(text, kind):
    """Yield (layout, is_cascade) for layout settings in front matter or config text."""
    if kind == "yaml":
        pattern, cascade = LAYOUT_YAML, CASCADE_YAML
    elif kind == "toml":
        pattern, cascade = LAYOUT_TOML, CASCADE_TOML
    else:
        pattern, cascade = LAYOUT_JSON, None
    for m in pattern.finditer(text):
        before = text[:m.start()]
        if cascade is not None:
            is_cascade = bool(cascade.search(before))
        else:
            is_cascade = '"cascade"' in before
        yield m.group(1), is_cascade


def scan_uses(root, content_dirs=None):
    """Find where layouts are set: content front matter, content adapters, config."""
    uses = {}
    adapters = []

    def add(layout, path, how):
        uses.setdefault(layout, []).append({"file": norm(os.path.relpath(path, root)), "how": how})

    if content_dirs is None:
        content_dirs = [os.path.join(root, "content")]
    for cdir in content_dirs:
        if not os.path.isdir(cdir):
            continue
        for dpath, dirs, files in os.walk(cdir):
            dirs.sort()
            for f in sorted(files):
                full = os.path.join(dpath, f)
                ext = os.path.splitext(f)[1].lower()
                if f.endswith(".gotmpl"):
                    adapters.append(norm(os.path.relpath(full, root)))
                    text = read_text(full)
                    seen = set()
                    for m in LAYOUT_GOTMPL.finditer(text):
                        seen.add(m.group(1))
                    for m in LAYOUT_JSON.finditer(text):
                        seen.add(m.group(1))
                    for name in sorted(seen):
                        add(name, full, "content adapter")
                elif ext in CONTENT_EXT:
                    fm, kind = front_matter(read_text(full, 65536))
                    if not fm:
                        continue
                    for name, is_cascade in _uses_in(fm, kind):
                        add(name, full, "cascade" if is_cascade else "front matter")
    config_files = []
    if os.path.isdir(root):
        for f in sorted(os.listdir(root)):
            if CONFIG_NAME.match(f) and os.path.isfile(os.path.join(root, f)):
                config_files.append(os.path.join(root, f))
    cfg_dir = os.path.join(root, "config")
    if os.path.isdir(cfg_dir):
        for dpath, dirs, files in os.walk(cfg_dir):
            dirs.sort()
            for f in sorted(files):
                if os.path.splitext(f)[1].lower() in CONFIG_EXT:
                    config_files.append(os.path.join(dpath, f))
    for full in config_files:
        ext = os.path.splitext(full)[1].lower()
        kind = {".yaml": "yaml", ".yml": "yaml", ".toml": "toml"}.get(ext, "json")
        for name, is_cascade in _uses_in(read_text(full), kind):
            add(name, full, "config cascade" if is_cascade else "config")
    return uses, adapters


def template_signals(text):
    """Signs that a template shows content the page body does not hold."""
    strong, weak = [], []
    if DATA_RE.search(text):
        strong.append("reads site data")
    if CHILD_RE.search(text):
        strong.append("lists child pages")
    if PARAMS_LIST_RE.search(text):
        strong.append("lists front matter values")
    elif PARAMS_RE.search(text):
        weak.append("uses front matter values")
    if SUMMARY_RE.search(text):
        weak.append("shows the summary or description")
    return strong, weak


def find_partial(name, layout_dirs):
    names = [name]
    if "." not in os.path.basename(name):
        names.append(name + ".html")
    for base in layout_dirs:
        for folder in ("_partials", "partials"):
            for n in names:
                p = os.path.join(base, folder, *n.split("/"))
                if os.path.isfile(p):
                    return p
    return None


def layout_signals(templates, layout_dirs):
    strong, weak, renders_content = [], [], False
    for t in templates:
        text = read_text(t["file"])
        if CONTENT_RE.search(text):
            renders_content = True
        s, w = template_signals(text)
        for x in s:
            if x not in strong:
                strong.append(x)
        for x in w:
            if x not in weak:
                weak.append(x)
        for pname in PARTIAL_RE.findall(text):
            p = find_partial(pname, layout_dirs)
            if p is None:
                continue
            ps, pw = template_signals(read_text(p))
            for x in ps + pw:
                label = "%s (in partial %s)" % (x, pname)
                if label not in weak:
                    weak.append(label)
    return strong, weak, renders_content


def describe_uses(uses, limit=5):
    shown = ["%s (%s)" % (u["file"], u["how"]) for u in uses[:limit]]
    more = len(uses) - limit
    if more > 0:
        shown.append("and %d more" % more)
    return ", ".join(shown)


def check_project(root, layout_dirs=None, content_dirs=None, md_format="markdown",
                  md_suffix="md", languages=None):
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        raise UsageError("not a folder: %s" % root)
    if not layout_dirs:
        layout_dirs = [os.path.join(root, "layouts")]
    layout_dirs = [os.path.abspath(d) for d in layout_dirs]
    for d in layout_dirs:
        if not os.path.isdir(d):
            raise UsageError("no layouts folder: %s" % d)
    if content_dirs:
        content_dirs = [os.path.abspath(d) for d in content_dirs]
    templates = collect_templates(layout_dirs, md_format, md_suffix, languages)
    md_templates = [t for t in templates if t["format"] == md_format]
    by_layout = {}
    for t in templates:
        if t["layout"] is None:
            continue
        e = by_layout.setdefault(t["layout"], {"html": [], "markdown": [], "other": []})
        if t["format"] == "html":
            e["html"].append(t)
        elif t["format"] == md_format:
            e["markdown"].append(t)
        else:
            e["other"].append(t)
    uses, adapters = scan_uses(root, content_dirs)

    findings = []
    layouts = []
    for name in sorted(by_layout):
        e = by_layout[name]
        entry = {
            "layout": name,
            "html_templates": [t["path"] for t in e["html"]],
            "markdown_templates": [t["path"] for t in e["markdown"]],
            "other_templates": [t["path"] for t in e["other"]],
            "uses": uses.get(name, []),
        }
        layouts.append(entry)
        if not md_templates or not e["html"] or e["markdown"]:
            continue
        strong, weak, renders_content = layout_signals(e["html"], layout_dirs)
        entry["signals"] = {"strong": strong, "weak": weak, "renders_content": renders_content}
        first = e["html"][0]
        target = "%s.%s.%s" % (name, md_format, md_suffix)
        if first["dir"]:
            target = first["dir"] + "/" + target
        html_list = ", ".join(entry["html_templates"])
        u = entry["uses"]
        if not u:
            code = "unused-layout"
            message = ('Layout "%s" has an HTML template (%s) but no Markdown template, and no '
                       'content front matter, content adapter or config file we read sets it. '
                       'A module, a type folder or another setting may still use it.'
                       % (name, html_list))
        elif strong:
            code = "layout-loses-content"
            message = ('Layout "%s" has an HTML template (%s) but no Markdown template. Pages that '
                       'use it (%s) get the generic Markdown template, which prints the page body; '
                       'this layout %s, so the Markdown copy will lack that content.'
                       % (name, html_list, describe_uses(u), " and ".join(strong)))
        else:
            code = "layout-no-markdown"
            detail = ("; the HTML template %s" % ", ".join(weak)) if weak else ""
            message = ('Layout "%s" has an HTML template (%s) but no Markdown template. Pages that '
                       'use it (%s) get the generic Markdown template%s. No sign of content outside '
                       'the page body was found, so the copy may be fine: compare one page\'s copy '
                       'with the page.' % (name, html_list, describe_uses(u), detail))
        findings.append({
            "code": code,
            "severity": SEVERITY[code],
            "layout": name,
            "templates": entry["html_templates"],
            "uses": u,
            "signals": entry["signals"],
            "message": message,
            "hint": ("Add layouts/%s that renders the same content as Markdown, or move the "
                     "content into the page body." % target),
        })
    if not md_templates:
        findings.append({
            "code": "no-markdown-output",
            "severity": "info",
            "layout": None,
            "templates": [],
            "uses": [],
            "signals": {},
            "message": ('No template for the "%s" output format (file names with ".%s." or ending '
                        'in ".%s") was found, so this project does not seem to build Markdown '
                        'copies. Nothing else was checked.' % (md_format, md_format, md_suffix)),
            "hint": "Use --format and --suffix if the project's Markdown output format has another name.",
        })
    order = {"error": 0, "warning": 1, "info": 2}
    findings.sort(key=lambda f: (order[f["severity"]], f["layout"] or ""))
    counts = {"error": 0, "warning": 0, "info": 0}
    for f in findings:
        counts[f["severity"]] += 1
    return {
        "tool": "hugo_layout_check",
        "version": VERSION,
        "root": norm(root),
        "format": md_format,
        "suffix": md_suffix,
        "templates": len(templates),
        "markdown_templates": sorted(t["path"] for t in md_templates),
        "content_adapters": adapters,
        "layouts": layouts,
        "findings": findings,
        "counts": counts,
    }


def render_text(report):
    lines = ["hugo_layout_check %s" % report["version"],
             "project: %s" % report["root"],
             "templates read: %d; %s templates: %d" % (report["templates"], report["format"],
                                                       len(report["markdown_templates"]))]
    for f in report["findings"]:
        lines.append("")
        lines.append("%s %s: %s" % (f["severity"].upper(), f["code"], f["message"]))
        lines.append("  fix: %s" % f["hint"])
    c = report["counts"]
    lines.append("")
    lines.append("%d error(s), %d warning(s), %d info. Each finding is a sign to check against the "
                 "built Markdown copy, not proof." % (c["error"], c["warning"], c["info"]))
    return "\n".join(lines) + "\n"


def main(argv=None, out=None):
    out = out or sys.stdout
    ap = argparse.ArgumentParser(
        description="Find Hugo page layouts that have an HTML template but no Markdown template.")
    ap.add_argument("root", help="the Hugo project folder (holds layouts/ and content/)")
    ap.add_argument("--layouts", action="append",
                    help="a layouts folder to read (repeat for theme or module layouts); "
                         "default: <root>/layouts")
    ap.add_argument("--content", action="append",
                    help="a content folder to scan for layout settings (repeatable); "
                         "default: <root>/content")
    ap.add_argument("--format", default="markdown",
                    help="name of the Markdown output format (default: markdown)")
    ap.add_argument("--suffix", default="md",
                    help="file suffix of the Markdown media type (default: md)")
    ap.add_argument("--languages",
                    help="comma-separated language keys used in template names; default: treat "
                         "any two-letter name such as 'de' or 'pt-br' as a language")
    ap.add_argument("--json", action="store_true", help="print the full report as JSON")
    ap.add_argument("--version", action="version", version="hugo_layout_check " + VERSION)
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    languages = None
    if args.languages:
        languages = {x.strip().lower() for x in args.languages.split(",") if x.strip()}
    try:
        report = check_project(args.root, args.layouts, args.content, args.format.lower(),
                               args.suffix.lower().lstrip("."), languages)
    except UsageError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    if args.json:
        out.write(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    else:
        out.write(render_text(report))
    return 1 if (report["counts"]["error"] or report["counts"]["warning"]) else 0


if __name__ == "__main__":
    sys.exit(main())
