#!/usr/bin/env python3
"""Generate Henrik's profile SVGs from public GitHub data.

The portrait is generated from assets/portrait-source.png by the jp2a wrapper
in scripts/generate_ascii_portrait.sh. This script fetches structured GitHub
data and renders deterministic light and dark SVGs. Neither step uses an LLM.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
PORTRAIT = ROOT / "assets" / "portrait.txt"
OUTPUTS = {
    "dark": ROOT / "assets" / "dark-mode.svg",
    "light": ROOT / "assets" / "light-mode.svg",
}
USERNAME = "henrikkvamme"
API_VERSION = "2022-11-28"


@dataclass(frozen=True)
class ActivityStats:
    active_days: int
    current_streak: int
    longest_streak: int


@dataclass(frozen=True)
class ProfileStats:
    public_repos: int
    original_repos: int
    followers: int
    stars: int
    top_repo: str
    top_repo_stars: int
    contributions: int
    commits: int
    pull_requests: int
    active_days: int
    current_streak: int
    longest_streak: int
    restricted_contributions: int = 0
    merged_pull_requests: int = 0

    @property
    def public_contributions(self) -> int:
        return max(0, self.contributions - self.restricted_contributions)


class GitHubClient:
    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get(
            "GH_TOKEN"
        )

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{USERNAME}-profile-generator",
            "X-GitHub-Api-Version": API_VERSION,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def request_json(
        self, url: str, *, payload: dict[str, Any] | None = None
    ) -> Any:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(url, data=body, headers=self._headers())
        if payload is not None:
            request.add_header("Content-Type", "application/json")

        for attempt in range(3):
            try:
                with urlopen(request, timeout=30) as response:
                    return json.load(response)
            except HTTPError as error:
                if error.code not in {429, 502, 503, 504} or attempt == 2:
                    raise
                time.sleep(2**attempt)
        raise RuntimeError("GitHub request failed after retries")

    def rest(self, path: str) -> Any:
        return self.request_json(f"https://api.github.com{path}")

    def graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        if not self.token:
            raise RuntimeError("GITHUB_TOKEN or GH_TOKEN is required for GraphQL")
        response = self.request_json(
            "https://api.github.com/graphql",
            payload={"query": query, "variables": variables},
        )
        if not isinstance(response, dict):
            raise RuntimeError("GitHub GraphQL returned a non-object response")
        if response.get("errors"):
            raise RuntimeError(f"GitHub GraphQL errors: {response['errors']}")
        return response

def calculate_activity(
    days: list[dict[str, Any]], *, today: dt.date | None = None
) -> ActivityStats:
    today = today or dt.date.today()
    counts = {
        dt.date.fromisoformat(str(day["date"])): int(day["contributionCount"])
        for day in days
    }
    active_days = sum(count > 0 for count in counts.values())

    longest_streak = 0
    running_streak = 0
    previous: dt.date | None = None
    for day, count in sorted(counts.items()):
        if count <= 0:
            running_streak = 0
        elif previous is not None and day == previous + dt.timedelta(days=1):
            running_streak += 1
        else:
            running_streak = 1
        longest_streak = max(longest_streak, running_streak)
        previous = day

    cursor = today if counts.get(today, 0) > 0 else today - dt.timedelta(days=1)
    current_streak = 0
    while counts.get(cursor, 0) > 0:
        current_streak += 1
        cursor -= dt.timedelta(days=1)

    return ActivityStats(active_days, current_streak, longest_streak)


def summarize_stats(
    user: dict[str, Any],
    repos: list[dict[str, Any]],
    contribution_data: dict[str, Any],
    *,
    today: dt.date | None = None,
) -> ProfileStats:
    original_repos = [repo for repo in repos if not bool(repo.get("fork"))]
    top_repo = max(
        original_repos,
        key=lambda repo: (int(repo.get("stargazers_count", 0)), str(repo["name"])),
        default={"name": "none", "stargazers_count": 0},
    )
    activity = calculate_activity(contribution_data["days"], today=today)

    return ProfileStats(
        public_repos=int(user["public_repos"]),
        original_repos=len(original_repos),
        followers=int(user["followers"]),
        stars=sum(int(repo.get("stargazers_count", 0)) for repo in original_repos),
        top_repo=str(top_repo["name"]),
        top_repo_stars=int(top_repo.get("stargazers_count", 0)),
        contributions=int(contribution_data["totalContributions"]),
        commits=int(contribution_data["totalCommitContributions"]),
        pull_requests=int(contribution_data["totalPullRequestContributions"]),
        active_days=activity.active_days,
        current_streak=activity.current_streak,
        longest_streak=activity.longest_streak,
        restricted_contributions=int(
            contribution_data.get("restrictedContributionsCount", 0)
        ),
        merged_pull_requests=int(contribution_data.get("mergedPullRequests", 0)),
    )


def fetch_stats(client: GitHubClient) -> ProfileStats:
    user = client.rest(f"/users/{USERNAME}")
    repos: list[dict[str, Any]] = []
    page = 1
    while True:
        batch = client.rest(
            f"/users/{USERNAME}/repos?per_page=100&type=owner&page={page}"
        )
        if not isinstance(batch, list):
            raise RuntimeError("GitHub REST returned an unexpected repository page")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    if not isinstance(user, dict):
        raise RuntimeError("GitHub REST returned an unexpected response")

    query = """
    query ProfileActivity($login: String!, $pullRequestQuery: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays { date contributionCount }
            }
          }
          restrictedContributionsCount
          totalCommitContributions
          totalPullRequestContributions
        }
      }
      pullRequests: search(query: $pullRequestQuery, type: ISSUE, first: 1) {
        issueCount
      }
    }
    """
    response = client.graphql(
        query,
        {
            "login": USERNAME,
            "pullRequestQuery": (
                f"author:{USERNAME} is:pr is:merged is:public"
            ),
        },
    )
    data = response["data"]
    collection = data["user"]["contributionsCollection"]
    calendar = collection["contributionCalendar"]
    days = [
        day
        for week in calendar["weeks"]
        for day in week["contributionDays"]
    ]
    contribution_data = {
        "totalContributions": calendar["totalContributions"],
        "restrictedContributionsCount": collection[
            "restrictedContributionsCount"
        ],
        "totalCommitContributions": collection["totalCommitContributions"],
        "totalPullRequestContributions": collection[
            "totalPullRequestContributions"
        ],
        "mergedPullRequests": data["pullRequests"]["issueCount"],
        "days": days,
    }
    return summarize_stats(user, repos, contribution_data)


def format_number(value: int) -> str:
    return f"{value:,}"


def row(y: int, label: str, value: str) -> str:
    dots = "." * max(3, 24 - len(label))
    return (
        f'<text x="430" y="{y}"><tspan class="muted">. </tspan>'
        f'<tspan class="key">{html.escape(label)}</tspan>:'
        f'<tspan class="muted"> {dots} </tspan>'
        f'<tspan class="value">{html.escape(value)}</tspan></text>'
    )


def section(y: int, label: str) -> str:
    rule = "-" * max(8, 61 - len(label))
    return (
        f'<text x="430" y="{y}" class="fg">- {html.escape(label)} '
        f'<tspan class="muted">{rule}</tspan></text>'
    )


def build_svg(stats: ProfileStats, portrait: list[str], *, theme: str) -> str:
    palettes = {
        "dark": {
            "background": "#161b22",
            "foreground": "#c9d1d9",
            "key": "#ffa657",
            "value": "#a5d6ff",
            "muted": "#616e7f",
            "accent": "#3fb950",
        },
        "light": {
            "background": "#f6f8fa",
            "foreground": "#24292f",
            "key": "#953800",
            "value": "#0550ae",
            "muted": "#6e7781",
            "accent": "#1a7f37",
        },
    }
    colors = palettes[theme]
    first_ascii_row = html.escape(portrait[0], quote=False)
    ascii_rows = [
        f'<tspan x="15" dy="18">{html.escape(line, quote=False)}</tspan>'
        for line in portrait[1:]
    ]

    current_streak = f"{stats.current_streak} days current"
    longest_streak = f"{stats.longest_streak} days longest"
    details = "\n  ".join(
        (
            '<text x="430" y="30" class="fg">henrik@github '
            '<tspan class="muted">----------------------------------------------------</tspan></text>',
            row(60, "OS", "macOS, Linux"),
            row(80, "Role", "Software engineer + startup builder"),
            row(100, "Company", "Texicon"),
            row(120, "Education", "Computer Science @ NTNU"),
            row(140, "Location", "Trondheim, Norway"),
            section(180, "Building"),
            row(210, "Devme", "Dev-stack supervisor for worktrees"),
            row(230, "Nixus", "Nix configuration + synchronized agent skills"),
            row(250, "Sambu", "Co-living app for students"),
            section(290, "GitHub"),
            row(
                320,
                "Contributions.1y",
                f"{format_number(stats.contributions)} total / "
                f"{format_number(stats.public_contributions)} public",
            ),
            row(
                340,
                "Output.1y",
                f"{format_number(stats.commits)} commits / "
                f"{format_number(stats.pull_requests)} pull requests",
            ),
            row(
                360,
                "Merged.PRs",
                f"{format_number(stats.merged_pull_requests)} public",
            ),
            row(
                380,
                "Projects",
                f"{stats.original_repos} original / {stats.public_repos} public repos",
            ),
            row(400, "Stars", f"{format_number(stats.stars)} on original repos"),
            row(420, "Streaks", f"{current_streak} / {longest_streak}"),
            row(440, "Active.Days.1y", format_number(stats.active_days)),
            row(460, "Followers", format_number(stats.followers)),
            row(
                480,
                "Top.Repository",
                f"{stats.top_repo} / {stats.top_repo_stars} stars",
            ),
            section(520, "Stack"),
            row(550, "Languages", "TypeScript, Python, Rust, Shell"),
            row(570, "Systems", "Nix, Docker, GitHub Actions, self-hosting"),
        )
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="600" viewBox="0 0 1120 600" role="img" aria-labelledby="title desc">
  <title id="title">Henrik Kvamme's GitHub profile</title>
  <desc id="desc">A portrait made from literal ASCII characters beside Henrik's work and automatically updated public GitHub statistics.</desc>
  <style>
    text {{ font-family: Consolas, "Liberation Mono", monospace; font-size: 15px; white-space: pre; fill: {colors['foreground']}; }}
    .fg, .ascii {{ fill: {colors['foreground']}; }}
    .key {{ fill: {colors['key']}; }}
    .value {{ fill: {colors['value']}; }}
    .muted {{ fill: {colors['muted']}; }}
    .accent {{ fill: {colors['accent']}; }}
  </style>
  <rect width="1120" height="600" rx="15" fill="{colors['background']}" />
  <g class="ascii" aria-label="ASCII portrait of Henrik Kvamme">
    <text x="15" y="30" xml:space="preserve">{first_ascii_row}{''.join(ascii_rows)}</text>
  </g>
  {details}
</svg>
'''


def load_portrait() -> list[str]:
    lines = PORTRAIT.read_text(encoding="ascii").splitlines()
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    if not lines:
        raise RuntimeError("ASCII portrait is empty")
    if any("StartNTNU" in line for line in lines):
        raise RuntimeError("ASCII portrait must not contain the StartNTNU logo")
    return lines


def main() -> None:
    stats = fetch_stats(GitHubClient())
    portrait = load_portrait()
    for theme, output in OUTPUTS.items():
        output.write_text(build_svg(stats, portrait, theme=theme), encoding="utf-8")
        print(f"Wrote {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
