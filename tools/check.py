"""Sanity-check every page: inline JavaScript parses, and internal links resolve.

Usage:  python tools/check.py [folder ...]     (run from the repo root; default = all pages)
Needs Node on PATH for the syntax check.
"""
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.S)
HREF = re.compile(r"""(?:href|src)=["'](/[^"'#?]*)""")
JSPATH = re.compile(r"""["'`](/(?:koningsdam/)?[a-z0-9-]+/(?:[a-z0-9-]+/)?)["'`]""")
DATA = re.compile(r"data:[a-z]+/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=]+")


def main():
    wanted = [a.strip("/") for a in sys.argv[1:]]
    bad = 0
    for path in sorted(ROOT.rglob("index.html")):
        folder = path.parent.relative_to(ROOT).as_posix()
        folder = "" if folder == "." else folder
        if wanted and folder not in wanted and not any(folder.startswith(w + "/") for w in wanted if w):
            continue
        html = DATA.sub("DATAURI", path.read_bytes().decode("utf-8"))
        problems = []
        for i, m in enumerate(SCRIPT.finditer(html)):
            code = m.group(1)
            if not code.strip():
                continue
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
                f.write(code)
            r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True)
            pathlib.Path(f.name).unlink(missing_ok=True)
            if r.returncode:
                problems.append(f"script #{i + 1}: " + r.stderr.strip().splitlines()[-1] + " | " + " ".join(r.stderr.split("\n")[1:3]).strip()[:160])
        for link in sorted(set(HREF.findall(html)) | set(JSPATH.findall(html))):
            target = ROOT / link.lstrip("/")
            if not (target.is_file() or (target / "index.html").is_file()):
                problems.append(f"broken internal link: {link}")
        for token in ("DATAURI_MISSING", "TODO", "UNCONFIRMED", "undefined</", ">undefined<"):
            if token in html:
                problems.append(f"leftover marker: {token}")
        size = path.stat().st_size // 1024
        print(f"{'FAIL' if problems else 'ok  '} /{folder + '/' if folder else ''}  ({size} KB)")
        for p in problems:
            print("       -", p)
        bad += bool(problems)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
