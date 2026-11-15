"""Stamp the shared site nav (tabs + sub-links) into every page.

Usage:  python tools/nav.py          (run from the repo root)

Each page is standalone HTML with the nav inlined, so this script is the single
source of truth for the nav markup and its CSS. It is safe to re-run.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

BRAND = "Diane's 70th"

# tab key -> (label, href, [(sub key, label, href), ...])
TABS = {
    "eurodam": ("Eurodam", "/", [
        ("guide", "Ship guide", "/"),
        ("ports", "Ports &amp; excursions", "/ports/"),
        ("dining", "Ship dining", "/dining/"),
        ("planner", "Trip planner", "/planner/"),
        ("trip", "Boston trip plan", "/trip/"),
    ]),
    "koningsdam": ("Koningsdam", "/koningsdam/", [
        ("guide", "Ship guide", "/koningsdam/"),
        ("ports", "Ports &amp; excursions", "/koningsdam/ports/"),
        ("dining", "Ship dining", "/koningsdam/dining/"),
        ("planner", "Trip planner", "/koningsdam/planner/"),
        ("trip", "Boston trip plan", "/koningsdam/trip/"),
    ]),
    "compare": ("Comparisons", "/finalists/", [
        ("finalists", "The 4 finalists", "/finalists/"),
        ("options", "All 13 options", "/options/"),
    ]),
}

# page folder (relative to the repo root, "" = home) -> (tab, sub)
PAGES = {
    "": ("eurodam", "guide"),
    "ports": ("eurodam", "ports"),
    "juneau": ("eurodam", "ports"),
    "icy-strait": ("eurodam", "ports"),
    "sitka": ("eurodam", "ports"),
    "ketchikan": ("eurodam", "ports"),
    "victoria": ("eurodam", "ports"),
    "dining": ("eurodam", "dining"),
    "planner": ("eurodam", "planner"),
    "trip": ("eurodam", "trip"),
    "finalists": ("compare", "finalists"),
    "options": ("compare", "options"),
    "koningsdam": ("koningsdam", "guide"),
    "koningsdam/dining": ("koningsdam", "dining"),
    "koningsdam/planner": ("koningsdam", "planner"),
    "koningsdam/trip": ("koningsdam", "trip"),
    # any other folder under koningsdam/ is a port page
}

CSS = """/*sitenav*/
.sitenav{background:#141b2b;color:#e8ebf0;font:600 13px/1.4 "Figtree","Segoe UI",system-ui,sans-serif}
.sitenav a{color:#c9d3e2;text-decoration:none}
.sitenav a:hover,.sitenav a:focus-visible{color:#fff}
.sn-top{display:flex;flex-wrap:wrap;align-items:flex-end;gap:0 4px;padding:8px max(16px,env(safe-area-inset-right,0px)) 0 max(16px,env(safe-area-inset-left,0px))}
.sn-top b{font-family:"Gloock",Georgia,serif;font-weight:400;font-size:16px;color:#ffc2a8;margin-right:14px;padding-bottom:9px;white-space:nowrap}
.sn-tab{padding:8px 16px 9px;border-radius:9px 9px 0 0;font-size:14px;white-space:nowrap}
.sn-tab[aria-current]{background:#253049;color:#fff;box-shadow:inset 0 3px 0 #ffc2a8}
.sn-sub{display:flex;flex-wrap:wrap;gap:4px 20px;padding:9px max(16px,env(safe-area-inset-right,0px)) 9px max(16px,env(safe-area-inset-left,0px));background:#253049}
.sn-sub a{padding:2px 0;border-bottom:2px solid transparent}
.sn-sub a[aria-current]{color:#fff;border-bottom-color:#ffc2a8}
@media (max-width:520px){.sn-top b{flex-basis:100%;padding-bottom:4px}.sn-tab{padding-inline:12px}}
@media print{.sitenav{display:none}}
/*endsitenav*/"""

OLD_CSS = re.compile(r"\.sitenav\{display:flex.*?\.sitenav a\[aria-current\]\{[^}]*\}", re.S)
NEW_CSS = re.compile(r"/\*sitenav\*/.*?/\*endsitenav\*/", re.S)
NAV = re.compile(r'<nav class="sitenav".*?</nav>', re.S)


def nav_html(tab, sub):
    cur_tab, cur_page = ' aria-current="true"', ' aria-current="page"'
    tabs = "".join(
        f'<a class="sn-tab" href="{href}"{cur_tab if key == tab else ""}>{label}</a>'
        for key, (label, href, _) in TABS.items()
    )
    subs = "".join(
        f'<a href="{href}"{cur_page if key == sub else ""}>{label}</a>'
        for key, label, href in TABS[tab][2]
    )
    return (
        f'<nav class="sitenav" aria-label="Site">'
        f'<div class="sn-top"><b>{BRAND}</b>{tabs}</div>'
        f'<div class="sn-sub" aria-label="{TABS[tab][0]} pages">{subs}</div></nav>'
    )


def main():
    bad = 0
    for path in sorted(ROOT.rglob("index.html")):
        folder = path.parent.relative_to(ROOT).as_posix()
        folder = "" if folder == "." else folder
        if folder.startswith(("tools", ".git")):
            continue
        where = PAGES.get(folder) or (("koningsdam", "ports") if folder.startswith("koningsdam/") else None)
        if not where:
            print("SKIP (not in PAGES):", folder)
            bad += 1
            continue
        src = path.read_bytes().decode("utf-8")
        css = CSS.replace("\n", "\r\n") if "\r\n" in src else CSS
        out, n_css = NEW_CSS.subn(lambda m: css, src, count=1)
        if not n_css:
            out, n_css = OLD_CSS.subn(lambda m: css, src, count=1)
        out, n_nav = NAV.subn(lambda m: nav_html(*where), out, count=1)
        if not (n_css and n_nav):
            print(f"FAILED {folder or '/'}: css={n_css} nav={n_nav}")
            bad += 1
            continue
        if out != src:
            path.write_bytes(out.encode("utf-8"))
        print(f"ok  /{folder + '/' if folder else ''}  ->  {where[0]} / {where[1]}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
