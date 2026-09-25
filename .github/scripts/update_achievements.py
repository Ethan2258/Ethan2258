"""Refresh the Achievements section of the profile README from the public profile page."""

from __future__ import annotations

import html
import re
import sys
import time
import urllib.request
from pathlib import Path


USER = "Ethan2258"
ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
ASSETS = ROOT / "assets" / "achievements"
START, END = "<!-- achievements:start -->", "<!-- achievements:end -->"
BADGE_LINK = re.compile(
    rf'<a href="/{USER}\?achievement=(?P<slug>[\w-]+)&amp;tab=achievements"[^>]*>(?P<body>.*?)</a>',
    re.S,
)
BADGE_IMAGE = re.compile(r'<img[^>]*src="(?P<src>[^"]+)"[^>]*alt="Achievement: (?P<name>[^"]+)"')
TIER = re.compile(r'achievement-tier-label[^>]*>\s*(?P<tier>x\d+)\s*<')


def fetch(url: str, attempts: int = 3) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": f"{USER}-profile-achievements"})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read()
        except OSError:
            if attempt + 1 == attempts:
                raise
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def parse_badges(page: str) -> dict[str, dict[str, str]]:
    """Return unlocked achievements keyed by slug, in the order the profile shows them."""
    badges: dict[str, dict[str, str]] = {}
    for link in BADGE_LINK.finditer(page):
        image = BADGE_IMAGE.search(link["body"])
        if image is None or link["slug"] in badges:
            continue
        tier = TIER.search(link["body"])
        badges[link["slug"]] = {
            "name": html.unescape(image["name"]),
            "image": html.unescape(image["src"]),
            "tier": tier["tier"] if tier else "",
        }
    return badges


def render(badges: dict[str, dict[str, str]]) -> str:
    lines = [START]
    for slug, badge in badges.items():
        label = f"{badge['name']} {badge['tier']}".strip()
        tier = f"<sup>{badge['tier']}</sup>" if badge["tier"] else ""
        lines.append(
            f'<a href="https://github.com/{USER}?tab=achievements&achievement={slug}">'
            f'<img src="assets/achievements/{slug}.png" alt="{label}" title="{label}" width="64"></a>{tier}'
        )
    lines.append(END)
    return "\n".join(lines)


def main() -> int:
    page = fetch(f"https://github.com/{USER}?tab=achievements").decode("utf-8")
    badges = parse_badges(page)
    if not badges:
        # An empty result almost always means the page layout changed; keep the current README.
        print("No achievements found on the profile page; leaving the README unchanged.", file=sys.stderr)
        return 1

    ASSETS.mkdir(parents=True, exist_ok=True)
    for slug, badge in badges.items():
        image = fetch(badge["image"])
        if not image.startswith(b"\x89PNG\r\n\x1a\n"):
            raise RuntimeError(f"{slug}: badge image is not a PNG")
        target = ASSETS / f"{slug}.png"
        if not target.is_file() or target.read_bytes() != image:
            target.write_bytes(image)
    for stale in ASSETS.glob("*.png"):
        if stale.stem not in badges:
            stale.unlink()

    readme = README.read_text(encoding="utf-8")
    if readme.count(START) != 1 or readme.count(END) != 1:
        raise RuntimeError("README.md must contain exactly one achievements marker pair")
    before, rest = readme.split(START)
    _, after = rest.split(END)
    updated = before + render(badges) + after
    if updated != readme:
        README.write_bytes(updated.encode("utf-8"))
    print("Achievements:", ", ".join(f"{b['name']} {b['tier']}".strip() for b in badges.values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
