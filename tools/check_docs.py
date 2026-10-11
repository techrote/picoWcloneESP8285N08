"""Offline documentation links, JSON and immutable public evidence checks."""
import hashlib
import json
import pathlib
import re
import sys
import unicodedata
from urllib.parse import unquote

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASELINE = ROOT / "evidence/FNR-002"
MANIFEST_SHA256 = "03b9dfe7e2e48571ee04673c96e545d2085a859ba05ffd9dc3b3a091060f938b"


def heading_ids(text):
    """GitHub-style anchors for this repository's plain-text headings."""
    seen = {}
    result = set()
    for heading in re.findall(r"^#{1,6}\s+(.+)$", text, re.MULTILINE):
        slug = "".join(
            char for char in heading.strip().lower()
            if char in "-_ " or unicodedata.category(char)[0] in "LN"
        ).replace(" ", "-")
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        result.add(f"{slug}-{count}" if count else slug)
    return result


def check():
    links = 0
    markdown = sorted(ROOT.glob("*.md")) + sorted((ROOT / "docs").rglob("*.md"))
    markdown += sorted((ROOT / "evidence").rglob("*.md"))
    for path in markdown:
        text = path.read_text(encoding="utf-8")
        if text.count("```") % 2:
            raise ValueError(f"Unbalanced code fences: {path.relative_to(ROOT)}")
        for destination in re.findall(r"\]\(([^)]+)\)", text):
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", destination):
                continue
            file, _, anchor = unquote(destination).partition("#")
            target = (path.parent / file).resolve() if file else path
            if not target.is_relative_to(ROOT):
                raise ValueError(f"Local link escapes repository: {destination}")
            if not target.exists():
                raise ValueError(f"Broken link in {path.relative_to(ROOT)}: {destination}")
            if anchor and target.suffix == ".md":
                if anchor not in heading_ids(target.read_text(encoding="utf-8")):
                    raise ValueError(f"Missing anchor in {path.relative_to(ROOT)}: {destination}")
            links += 1

    manifest = BASELINE / "SHA256SUMS"
    if hashlib.sha256(manifest.read_bytes()).hexdigest() != MANIFEST_SHA256:
        raise ValueError("Historical evidence manifest changed")
    entries = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, name = line.split(maxsplit=1)
        name = name.lstrip("*")
        if name in entries or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Invalid/duplicate evidence manifest entry")
        target = (BASELINE / name).resolve()
        if target.parent != BASELINE or not target.is_file():
            raise ValueError(f"Invalid evidence path: {name}")
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Historical evidence changed: {name}")
        entries[name] = digest
    expected = {path.name for path in BASELINE.iterdir() if path.is_file()}
    if set(entries) != expected - {"SHA256SUMS"}:
        raise ValueError("Evidence files and manifest entries differ")

    json_files = sorted((ROOT / "evidence").rglob("*.json"))
    for path in json_files:
        json.loads(path.read_text(encoding="utf-8"))
    print(f"PASS: {links} local links/anchors, {len(entries)} evidence hashes, "
          f"{len(json_files)} JSON files")


if __name__ == "__main__":
    try:
        check()
    except (ValueError, OSError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
