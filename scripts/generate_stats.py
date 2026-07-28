#!/usr/bin/env python3
"""Render the GitHub stat cards used by the profile README.

Writes assets/stats.svg and assets/langs.svg using the same palette and type
scale as johannes-schieder.com, so the cards look like the site rather than
like everyone else's profile.

Everything comes from the public REST API, so this runs locally without a
token too (just against a lower rate limit). GITHUB_TOKEN is used when set.

    python3 scripts/generate_stats.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

USER = os.environ.get("GH_USER", "JSchOBL")
API = "https://api.github.com"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "assets")

# src/styles/colors.ts of the portfolio site
NAVY = "#0a192f"
LIGHT_NAVY = "#112240"
LIGHTER_NAVY = "#233554"
SLATE = "#8892b0"
LIGHT_SLATE = "#a8b2d8"
LIGHTEST_SLATE = "#ccd6f6"
WHITE = "#e6f1ff"
GREEN = "#64ffda"

MONO = "ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SANS = "Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

# linguist colours, only for the languages that actually show up
LANG_COLORS = {
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "Python": "#3572A5",
    "Java": "#b07219",
    "Kotlin": "#A97BFF",
    "C++": "#f34b7d",
    "C": "#555555",
    "C#": "#178600",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Swift": "#F05138",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "HTML": "#e34c26",
    "CSS": "#663399",
    "SCSS": "#c6538c",
    "Vue": "#41b883",
    "Shell": "#89e051",
    "Dockerfile": "#384d54",
    "HCL": "#844FBA",
    "Makefile": "#427819",
    "Batchfile": "#C1F12E",
    "Jupyter Notebook": "#DA5B0B",
    "TeX": "#3D6117",
    "CMake": "#DA3434",
    "Nix": "#7e7eff",
    "Lua": "#000080",
    "Other": LIGHTER_NAVY,
}


def get(path: str) -> dict | list:
    url = path if path.startswith("http") else API + path
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USER}-profile-readme",
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def search_count(query: str) -> int:
    """Total hits for a search query, 0 if the endpoint refuses us."""
    try:
        return int(get(f"/search/issues?q={query}&per_page=1")["total_count"])
    except (urllib.error.HTTPError, urllib.error.URLError, KeyError, ValueError) as exc:
        print(f"  ! search '{query}' failed: {exc}", file=sys.stderr)
        return 0


def commit_count() -> int:
    try:
        return int(get(f"/search/commits?q=author:{USER}&per_page=1")["total_count"])
    except (urllib.error.HTTPError, urllib.error.URLError, KeyError, ValueError) as exc:
        print(f"  ! commit search failed: {exc}", file=sys.stderr)
        return 0


def esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


def collect() -> dict:
    user = get(f"/users/{USER}")
    repos: list[dict] = []
    page = 1
    while True:
        batch = get(f"/users/{USER}/repos?per_page=100&page={page}&sort=pushed")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    owned = [r for r in repos if not r["fork"] and not r["archived"]]
    stars = sum(r["stargazers_count"] for r in owned)

    # Language share is normalised per repository before summing: one repo full
    # of generated notebooks shouldn't outweigh every other language on the
    # profile. Each repo gets one vote, split across the languages in it.
    weights: dict[str, float] = {}
    for repo in repos:
        if repo["archived"] or repo["name"] == USER:
            continue
        try:
            langs = get(repo["languages_url"])
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            print(f"  ! languages for {repo['name']} failed: {exc}", file=sys.stderr)
            continue
        total = sum(langs.values())
        if not total:
            continue
        for name, size in langs.items():
            weights[name] = weights.get(name, 0.0) + size / total

    grand = sum(weights.values()) or 1.0
    ranked = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)
    top = [(name, 100 * value / grand) for name, value in ranked[:8]]
    rest = sum(value for _, value in ranked[8:])
    if rest:
        top.append(("Other", 100 * rest / grand))

    return {
        "name": user.get("name") or USER,
        "repos": user["public_repos"],
        "followers": user["followers"],
        "stars": stars,
        "commits": commit_count(),
        "prs": search_count(f"author:{USER}+type:pr"),
        "merged": search_count(f"author:{USER}+type:pr+is:merged"),
        "langs": top,
    }


def base_style() -> str:
    return f"""
    .card {{ fill: {NAVY}; stroke: {LIGHTER_NAVY}; }}
    .mono {{ font-family: {MONO}; }}
    .sans {{ font-family: {SANS}; }}
    .prompt {{ font-size: 13px; fill: {GREEN}; }}
    .caret {{ fill: {GREEN}; animation: blink 1.1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    @keyframes rise {{ from {{ opacity: 0; transform: translateY(10px); }}
                       to {{ opacity: 1; transform: translateY(0); }} }}
    .rise {{ animation: rise .55s cubic-bezier(.2,.8,.2,1) both; }}
    @media (prefers-reduced-motion: reduce) {{
      .rise, .caret, .grow {{ animation: none; opacity: 1; }}
    }}
"""


def render_stats(data: dict) -> str:
    tiles = [
        ("Repositories", data["repos"]),
        ("Commits", data["commits"]),
        ("Pull requests", data["prs"]),
        ("Merged", data["merged"]),
        ("Stars earned", data["stars"]),
        ("Followers", data["followers"]),
    ]
    width, height = 900, 208
    pad, gap = 28, 14
    tile_w = (width - 2 * pad - gap * (len(tiles) - 1)) / len(tiles)
    tile_h, tile_y = 92, 88

    parts = []
    for i, (label, value) in enumerate(tiles):
        x = pad + i * (tile_w + gap)
        cx = x + tile_w / 2
        parts.append(f"""  <g class="rise" style="animation-delay:{0.06 * i + 0.15:.2f}s">
    <rect x="{x:.1f}" y="{tile_y}" width="{tile_w:.1f}" height="{tile_h}" rx="6"
          fill="{LIGHT_NAVY}" stroke="{LIGHTER_NAVY}"/>
    <rect x="{x:.1f}" y="{tile_y}" width="{tile_w:.1f}" height="2" rx="1" fill="{GREEN}" opacity=".55"/>
    <text class="sans" x="{cx:.1f}" y="{tile_y + 46}" text-anchor="middle"
          font-size="30" font-weight="700" fill="{WHITE}">{value}</text>
    <text class="mono" x="{cx:.1f}" y="{tile_y + 70}" text-anchor="middle"
          font-size="10.5" letter-spacing="1.1" fill="{SLATE}">{esc(label.upper())}</text>
  </g>""")

    stamp = datetime.now(timezone.utc).strftime("%d %b %Y")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}" role="img"
     aria-label="GitHub statistics for {esc(data['name'])}">
  <title>GitHub statistics for {esc(data['name'])}</title>
  <style>{base_style()}</style>
  <rect class="card" x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="10"/>
  <text class="mono prompt" x="{pad}" y="40">$ gh stats --user {esc(USER)}</text>
  <rect class="caret" x="{pad + 8.05 * len('$ gh stats --user ' + USER) + 4:.0f}" y="29" width="8" height="14" rx="1"/>
  <text class="mono" x="{pad}" y="64" font-size="12" fill="{SLATE}">
    all-time activity across public repositories</text>
  <text class="mono" x="{width - pad}" y="64" font-size="10.5" text-anchor="end"
        fill="{SLATE}" opacity=".5">updated {stamp}</text>
{chr(10).join(parts)}
</svg>
"""


def render_langs(data: dict) -> str:
    langs = data["langs"]
    width, height = 900, 214
    pad = 28
    bar_y, bar_h, bar_w = 78, 12, width - 2 * pad

    segments, legend, offset = [], [], 0.0
    for i, (name, pct) in enumerate(langs):
        seg_w = max(bar_w * pct / 100, 2.0)
        color = LANG_COLORS.get(name, SLATE)
        segments.append(f"""    <rect x="{pad + offset:.2f}" y="{bar_y}" width="{seg_w:.2f}" height="{bar_h}"
          fill="{color}" class="rise" style="animation-delay:{0.05 * i + 0.2:.2f}s"/>""")
        offset += seg_w

        col, row = i % 3, i // 3
        lx = pad + col * ((width - 2 * pad) / 3)
        ly = 132 + row * 30
        legend.append(f"""  <g class="rise" style="animation-delay:{0.05 * i + 0.3:.2f}s">
    <rect x="{lx:.1f}" y="{ly - 9}" width="10" height="10" rx="2.5" fill="{color}"/>
    <text class="mono" x="{lx + 20:.1f}" y="{ly}" font-size="12.5" fill="{LIGHTEST_SLATE}">{esc(name)}</text>
    <text class="mono" x="{lx + 20 + 7.7 * len(name) + 10:.1f}" y="{ly}" font-size="12.5"
          fill="{SLATE}">{pct:.1f}%</text>
  </g>""")

    rows = (len(langs) + 2) // 3
    height = 132 + rows * 30 + 16

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}" role="img"
     aria-label="Most used languages by {esc(data['name'])}">
  <title>Most used languages by {esc(data['name'])}</title>
  <style>{base_style()}</style>
  <rect class="card" x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="10"/>
  <text class="mono prompt" x="{pad}" y="40">$ gh langs --weighted</text>
  <rect class="caret" x="{pad + 8.05 * len('$ gh langs --weighted') + 4:.0f}" y="29" width="8" height="14" rx="1"/>
  <text class="mono" x="{pad}" y="62" font-size="12" fill="{SLATE}">
    share of each repository, so one big repo can't drown out the rest</text>
  <clipPath id="bar"><rect x="{pad}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="6"/></clipPath>
  <g clip-path="url(#bar)">
    <rect x="{pad}" y="{bar_y}" width="{bar_w}" height="{bar_h}" fill="{LIGHT_NAVY}"/>
{chr(10).join(segments)}
  </g>
{chr(10).join(legend)}
</svg>
"""


def main() -> int:
    print(f"collecting stats for {USER} ...")
    data = collect()
    print(f"  {data['repos']} repos, {data['commits']} commits, "
          f"{data['prs']} PRs, {len(data['langs'])} languages")

    os.makedirs(OUT, exist_ok=True)
    for filename, svg in (("stats.svg", render_stats(data)),
                          ("langs.svg", render_langs(data))):
        with open(os.path.join(OUT, filename), "w", encoding="utf-8") as handle:
            handle.write(svg)
        print(f"  wrote assets/{filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
