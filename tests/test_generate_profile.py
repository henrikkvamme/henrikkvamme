from __future__ import annotations

import datetime as dt
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "generate_profile", ROOT / "scripts" / "generate_profile.py"
)
assert SPEC and SPEC.loader
generate_profile = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = generate_profile
SPEC.loader.exec_module(generate_profile)


class ActivityTests(unittest.TestCase):
    def test_calculates_current_and_longest_streaks(self) -> None:
        days = [
            {"date": "2026-07-05", "contributionCount": 1},
            {"date": "2026-07-06", "contributionCount": 1},
            {"date": "2026-07-07", "contributionCount": 0},
            {"date": "2026-07-08", "contributionCount": 2},
            {"date": "2026-07-09", "contributionCount": 3},
            {"date": "2026-07-10", "contributionCount": 4},
        ]

        activity = generate_profile.calculate_activity(
            days, today=dt.date(2026, 7, 10)
        )

        self.assertEqual(activity.active_days, 5)
        self.assertEqual(activity.current_streak, 3)
        self.assertEqual(activity.longest_streak, 3)

    def test_current_streak_uses_yesterday_when_today_is_empty(self) -> None:
        days = [
            {"date": "2026-07-08", "contributionCount": 2},
            {"date": "2026-07-09", "contributionCount": 3},
            {"date": "2026-07-10", "contributionCount": 0},
        ]

        activity = generate_profile.calculate_activity(
            days, today=dt.date(2026, 7, 10)
        )

        self.assertEqual(activity.current_streak, 2)


class ProfileStatsTests(unittest.TestCase):
    def test_summarizes_public_original_repositories(self) -> None:
        user = {"public_repos": 3, "followers": 47}
        repos = [
            {"name": "alpha", "fork": False, "stargazers_count": 4},
            {"name": "beta", "fork": False, "stargazers_count": 11},
            {"name": "fork", "fork": True, "stargazers_count": 99},
        ]
        contribution_data = {
            "totalContributions": 2465,
            "totalCommitContributions": 821,
            "totalPullRequestContributions": 37,
            "days": [
                {"date": "2026-07-12", "contributionCount": 14},
                {"date": "2026-07-13", "contributionCount": 10},
            ],
        }

        stats = generate_profile.summarize_stats(
            user, repos, contribution_data, today=dt.date(2026, 7, 13)
        )

        self.assertEqual(stats.public_repos, 3)
        self.assertEqual(stats.original_repos, 2)
        self.assertEqual(stats.stars, 15)
        self.assertEqual(stats.top_repo, "beta")
        self.assertEqual(stats.top_repo_stars, 11)
        self.assertEqual(stats.contributions, 2465)
        self.assertEqual(stats.current_streak, 2)

class SvgTests(unittest.TestCase):
    def test_portrait_is_emitted_as_literal_ascii_text(self) -> None:
        stats = generate_profile.ProfileStats(
            public_repos=55,
            original_repos=51,
            followers=47,
            stars=40,
            top_repo="youtube-voice-go",
            top_repo_stars=11,
            contributions=2465,
            commits=821,
            pull_requests=37,
            active_days=200,
            current_streak=8,
            longest_streak=17,
        )

        svg = generate_profile.build_svg(
            stats, ["  .-:/+osyhdmN", "  literal ASCII"], theme="dark"
        )

        self.assertIn('<g class="ascii"', svg)
        self.assertIn(".-:/+osyhdmN", svg)
        self.assertIn("Devme", svg)
        self.assertIn("Nixus", svg)
        self.assertIn("Sambu", svg)
        self.assertNotIn("Henteplan", svg)
        self.assertNotIn("Folio MCP", svg)
        self.assertNotIn("portrait-glyph", svg)
        self.assertNotIn("<use ", svg)


if __name__ == "__main__":
    unittest.main()
