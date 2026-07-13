#!/usr/bin/env python3
"""Generate the terminal-style SVG used by the profile README."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "profile-terminal.svg"
PORTRAIT = ROOT / "assets" / "portrait-fragment.svg"
USERNAME = "henrikkvamme"

FALLBACK = {
    "public_repos": 55,
    "followers": 47,
    "stars": 40,
}


def github_json(path: str) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USERNAME}-profile-generator",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.github.com{path}", headers=headers)
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def profile_stats() -> dict[str, int]:
    try:
        user = github_json(f"/users/{USERNAME}")
        assert isinstance(user, dict)
        repos: list[object] = []
        page = 1
        while True:
            batch = github_json(
                f"/users/{USERNAME}/repos?per_page=100&type=owner&page={page}"
            )
            assert isinstance(batch, list)
            repos.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return {
            "public_repos": int(user["public_repos"]),
            "followers": int(user["followers"]),
            "stars": sum(
                int(repo.get("stargazers_count", 0))
                for repo in repos
                if isinstance(repo, dict) and not repo.get("fork", False)
            ),
        }
    except (AssertionError, HTTPError, KeyError, TypeError, URLError, ValueError) as error:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            raise RuntimeError("Could not refresh GitHub profile data") from error
        print(f"GitHub data unavailable, using fallback stats: {error}")
        return FALLBACK.copy()


def text(x: int, y: int, value: str, css_class: str = "value") -> str:
    return f'<text x="{x}" y="{y}" class="{css_class}">{value}</text>'


def row(y: int, label: str, value: str) -> str:
    return "\n".join(
        (
            text(520, y, label, "label"),
            text(650, y, "·" * 9, "dots"),
            text(748, y, value, "value"),
        )
    )


def section(y: int, title: str) -> str:
    return "\n".join(
        (
            text(520, y, f"- {title} ", "section"),
            f'<line x1="640" y1="{y - 5}" x2="1144" y2="{y - 5}" class="rule" />',
        )
    )


def build_svg(stats: dict[str, int], portrait_svg: str) -> str:
    details = "\n".join(
        (
            '<text x="520" y="74" class="prompt-user">henrik</text>',
            '<text x="582" y="74" class="prompt-muted">@trondheim</text>',
            section(114, "Profile"),
            row(146, "OS", "macOS, Linux"),
            row(172, "Role", "Full-stack developer @ Texicon"),
            row(198, "Education", "Computer Science @ NTNU"),
            row(224, "Location", "Trondheim, Norway"),
            row(250, "Focus", "Local-first tools, Nix, agent infrastructure"),
            section(294, "Stack"),
            row(326, "Languages", "Rust, TypeScript, Nix, Shell"),
            row(352, "Apps", "Tauri, React, native macOS"),
            row(378, "Systems", "Nix, Home Manager, Git"),
            row(404, "Infra", "Docker, self-hosting, VPS"),
            section(448, "Building"),
            row(480, "Current", "macOS-first Nix &amp; agent tooling"),
            section(524, "Contact"),
            row(556, "Web", "henrikkvamme.no"),
            row(582, "Email", "henrik.halvorsen.kvamme@gmail.com"),
        )
    )

    stats_line = (
        f'{stats["public_repos"]} repositories'
        f'  ·  {stats["stars"]} stars'
        f'  ·  {stats["followers"]} followers'
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="640" viewBox="0 0 1200 640" role="img" aria-labelledby="title description">
  <title id="title">Henrik Kvamme's terminal-style profile</title>
  <desc id="description">An ASCII portrait of Henrik beside a terminal-inspired summary of his work, technology stack, projects, and GitHub statistics.</desc>
  <defs>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="130%">
      <feDropShadow dx="0" dy="12" stdDeviation="18" flood-color="#010409" flood-opacity="0.42" />
    </filter>
    <linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0d1117" />
      <stop offset="1" stop-color="#111923" />
    </linearGradient>
  </defs>
  <style>
    text {{ font-family: SFMono-Regular, Consolas, "Liberation Mono", monospace; font-size: 15px; }}
    .window-title {{ fill: #8b949e; font-size: 13px; }}
    .portrait-name {{ fill: #f0f6fc; font-size: 19px; font-weight: 700; }}
    .portrait-role {{ fill: #8b949e; font-size: 13px; }}
    .prompt-user {{ fill: #7ee787; font-size: 17px; font-weight: 700; }}
    .prompt-muted {{ fill: #8b949e; font-size: 17px; }}
    .section {{ fill: #c9d1d9; font-size: 15px; font-weight: 700; }}
    .label {{ fill: #ffa657; }}
    .dots {{ fill: #484f58; letter-spacing: 2px; }}
    .value {{ fill: #a5d6ff; }}
    .rule {{ stroke: #30363d; stroke-width: 1; }}
    .stats {{ fill: #7ee787; font-size: 14px; }}
  </style>
  <rect width="1200" height="640" rx="18" fill="#010409" />
  <rect x="12" y="12" width="1176" height="616" rx="14" fill="url(#panel)" stroke="#30363d" filter="url(#shadow)" />
  <circle cx="42" cy="42" r="7" fill="#ff5f56" />
  <circle cx="66" cy="42" r="7" fill="#ffbd2e" />
  <circle cx="90" cy="42" r="7" fill="#27c93f" />
  <text x="600" y="47" text-anchor="middle" class="window-title">henrikkvamme / README.md</text>
  <line x1="12" y1="66" x2="1188" y2="66" class="rule" />
  <line x1="488" y1="66" x2="488" y2="604" class="rule" />
  {portrait_svg}
  <text x="244" y="548" text-anchor="middle" class="portrait-name">Henrik Kvamme</text>
  <text x="244" y="572" text-anchor="middle" class="portrait-role">full-stack developer · builder</text>
  {details}
  <line x1="40" y1="604" x2="1144" y2="604" class="rule" />
  <text x="600" y="624" text-anchor="middle" class="stats">GitHub  ·  {stats_line}</text>
</svg>
'''


def main() -> None:
    portrait = PORTRAIT.read_text(encoding="utf-8")
    svg = build_svg(profile_stats(), portrait)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
