# Andrew6rant profile implementation and Henrik profile metrics

Observed on 2026-07-13. GitHub counts are snapshots and will change.

## Executive recommendation

Copy Andrew's layout technique, not his metric definitions:

1. Keep the portrait as a hand-approved, static block of real SVG text. Do not regenerate it in the daily workflow.
2. Generate the surrounding SVG from one deterministic template and update only well-defined metrics.
3. Prefer metrics that communicate shipped work: 12-month contributions, public merged pull requests, stars on original public repositories, Henteplan provider coverage, and Folio MCP tool count.
4. Do not copy Andrew's all-time commit, "contributed repositories", or lines-of-code calculations. Their labels overstate what the underlying queries measure.

For the portrait, the important new fact is that Andrew's repository contains no image-to-ASCII implementation to reproduce. His current portrait is 25 manually embedded text rows. A good Henrik portrait therefore requires a separate, high-quality one-time conversion and manual cleanup, with the `StartNTNU` chest text excluded before conversion.

## How Andrew's profile is actually rendered

The profile README is only a linked `<picture>` element. It selects `dark_mode.svg` or `light_mode.svg` using `prefers-color-scheme`; the fallback is the light SVG. This is the same technique documented in GitHub's official profile README quickstart.

Sources:

- [Andrew's README at the inspected commit](https://github.com/Andrew6rant/Andrew6rant/blob/e059bd772121adab3f2a8c7c49d75303d8f39164/README.md)
- [GitHub's official profile README quickstart](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/quickstart-for-writing-on-github)
- [GitHub's official profile README requirements](https://docs.github.com/en/account-and-profile/how-tos/profile-customization/managing-your-profile-readme)

The dark card is a fixed 985 by 530 SVG. It uses a monospace font stack, a rounded background rectangle, and ordinary `<text>` and `<tspan>` elements with `white-space: pre`. The portrait is 25 static `<tspan>` rows at x=15, spaced 20 pixels vertically. The information panel begins at x=390. The portrait is not a raster image, a traced path, or a generated artifact.

Sources:

- [Static portrait rows and SVG text styling](https://github.com/Andrew6rant/Andrew6rant/blob/e059bd772121adab3f2a8c7c49d75303d8f39164/dark_mode.svg#L1-L46)
- [Information panel and metric IDs](https://github.com/Andrew6rant/Andrew6rant/blob/e059bd772121adab3f2a8c7c49d75303d8f39164/dark_mode.svg#L46-L71)
- [The 2022 commit titled "Update ASCII art"](https://github.com/Andrew6rant/Andrew6rant/commit/f44d8d02f5e57a02393b5af7007729895ff52298)

The current repository has no portrait source photo, conversion command, character palette, or image-processing dependency. Its history proves that portrait rows were replaced, but not how the replacement was produced. An older `test_ascii.png` in history is only a raster preview and does not establish the original converter. The exact conversion algorithm therefore cannot be recovered from the available primary source.

### What the daily automation changes

`today.py` parses both SVG files with lxml and replaces only named metric `<tspan>` elements and their dot padding. The portrait rows have no IDs and are never touched. The workflow runs the script at `0 4 * * *`, commits generated changes, and pushes them.

Sources:

- [SVG overwrite implementation](https://github.com/Andrew6rant/Andrew6rant/blob/e059bd772121adab3f2a8c7c49d75303d8f39164/today.py#L319-L359)
- [Updater entry point](https://github.com/Andrew6rant/Andrew6rant/blob/e059bd772121adab3f2a8c7c49d75303d8f39164/today.py#L440-L471)
- [Scheduled workflow](https://github.com/Andrew6rant/Andrew6rant/blob/e059bd772121adab3f2a8c7c49d75303d8f39164/.github/workflows/build.yaml)
- [Official scheduled workflow behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)

GitHub notes that scheduled workflows run from the default branch and can be delayed during high load. A non-round-minute time such as Henrik's existing `17 5 * * *` is sensible.

## Problems with Andrew's dynamic labels

Andrew's implementation is visually effective, but several displayed names are broader than the data:

- **Stars** sums only the first 100 repository edges even though the query requests `pageInfo`. It becomes incomplete for users with more than 100 matching repositories.
- **Contributed** is the total count of repositories accessible under `OWNER`, `COLLABORATOR`, and `ORGANIZATION_MEMBER`. It is not a count of repositories with a demonstrated contribution.
- **Commits** scans cached default-branch histories. This is affected by merge, squash, rebasing, branch deletion, attribution, and repository visibility.
- **Lines of Code on GitHub** adds and subtracts commit diff statistics. That measures churn across scanned history, not authored source size. Generated files, vendored files, merges, rewrites, and deletions make the headline misleading.
- The script contains a clean `contributionsCollection.contributionCalendar.totalContributions` query, but its main path does not call it.

Sources:

- [Repository and star query](https://github.com/Andrew6rant/Andrew6rant/blob/e059bd772121adab3f2a8c7c49d75303d8f39164/today.py#L53-L106)
- [Commit-history and line-change query](https://github.com/Andrew6rant/Andrew6rant/blob/e059bd772121adab3f2a8c7c49d75303d8f39164/today.py#L109-L261)
- [Official GraphQL pagination guidance](https://docs.github.com/en/enterprise-cloud@latest/graphql/guides/using-pagination-in-the-graphql-api)

## Henrik's truthful, deterministic metrics

The following values were computed from Henrik's public GitHub data on 2026-07-13. Dynamic profile metrics should include a generated date or clearly state their rolling window.

| Metric | Snapshot | Exact definition | Recommendation |
|---|---:|---|---|
| 12-month contributions | 2,465 total; 1,581 restricted; 884 public-derived | `contributionCalendar.totalContributions`, with `restrictedContributionsCount` reported separately | Strongest activity metric if labeled `12mo contributions`. Never describe all 2,465 as public commits. For a public-only card, use 884. |
| Public merged PRs | 115 | GraphQL search `author:henrikkvamme is:pr is:merged is:public`, using `issueCount` | Strong and legible. Label it `public merged PRs`, not open source PRs. |
| Stars on original public repositories | 40 | Sum `stargazerCount` across public owner repositories after excluding forks | Good compact proof of adoption. The non-fork condition must be explicit in code. |
| Original public repositories | 50 | 55 public owner repositories minus 5 forks | Accurate but less interesting than shipped-project metrics. Label `public projects` or `original public repos`. |
| Followers | 47 | Public user follower count | Accurate, but it is a vanity metric. Keep only if the layout needs a fifth general statistic. |
| Henteplan providers | 13 | Versioned provider registry and project README | Excellent project proof point: `13 waste providers`. |
| Henteplan municipality coverage | 265+ | Project-maintained documented coverage | Visually impressive, but intentionally approximate. Keep the plus sign and do not silently turn it into an exact count. |
| Folio MCP tools | 14 | Count of `server.registerTool(...)` calls in the inspected source | Excellent deterministic project proof point: `14 MCP tools`. |

Primary sources for GitHub definitions and visibility:

- [Official GraphQL User and ContributionsCollection fields](https://docs.github.com/en/graphql/reference/users)
- [Official GraphQL Repository fields](https://docs.github.com/en/graphql/reference/repos)
- [Official issue and pull request search qualifiers](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/filtering-and-searching-issues-and-pull-requests)
- [Official profile contribution rules](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference)
- [Official explanation of contributions on profiles](https://docs.github.com/en/account-and-profile/concepts/contributions-on-your-profile)
- [Official private contribution visibility settings](https://docs.github.com/en/account-and-profile/how-tos/contribution-settings/manage-visibility-settings-for-private-contributions-and-achievements)
- [Official REST endpoint for a user's public repositories](https://docs.github.com/en/rest/repos/repos#list-repositories-for-a-user)
- [Official starring API](https://docs.github.com/en/rest/activity/starring)

Primary sources for project-specific proof points:

- [Henteplan README at the inspected commit](https://github.com/henrikkvamme/henteplan/blob/a9059ab7fefc113f307dde91d33c1fad1d7497e6/README.md#L20-L26)
- [Folio MCP tool table at the inspected commit](https://github.com/henrikkvamme/folio-mcp/blob/180ca224ce287f340a202db5b533ad1290414d6a/README.md#L22-L32)
- [Folio MCP tool registrations at the inspected commit](https://github.com/henrikkvamme/folio-mcp/blob/180ca224ce287f340a202db5b533ad1290414d6a/src/server.ts)

### Suggested card content

A focused card would read more like proof of work than a generic terminal biography:

```text
henrik@github
Role ................. Software engineer + startup builder
Location ............................... Trondheim, Norway

Building
Henteplan ............. 13 providers / 265+ municipalities
Folio MCP ................................. 14 MCP tools

GitHub
12mo contributions ................................. 884 public
Public merged PRs ......................................... 115
Stars on original public repos ............................. 40
```

The `Building` lines should link to their repositories in the surrounding README or via separate text below the image. SVG-in-image links are less predictable on GitHub than normal Markdown links.

## Deterministic updater design

1. Store the approved logo-free ASCII portrait as a static fragment or literal array. The workflow must never regenerate it.
2. Render both theme SVGs from one template so rows and spacing cannot drift.
3. Fetch GitHub data with GraphQL connections and paginate until `hasNextPage` is false. Use GraphQL Search `issueCount` for public merged PRs.
4. Decide privacy explicitly:
   - Public-only mode: use public repository data and public contribution counts.
   - Profile-equivalent mode: use total contributions plus the restricted count, but label the total as contributions and never expose private repository details.
5. Compute project proof points from versioned source data, not prose where possible. Count Folio tool registrations from the syntax tree or a maintained tool registry. Count Henteplan providers from its provider registry.
6. Use the built-in `GITHUB_TOKEN` with the minimum `contents: write` workflow permission unless private-profile-equivalent contribution totals are deliberately required. Only introduce a personal token for a documented capability the built-in token cannot provide.
7. Commit only when generated SVGs actually change.

Official token guidance:

- [Automatic `GITHUB_TOKEN` authentication](https://docs.github.com/en/actions/concepts/security/github_token)
- [Using `GITHUB_TOKEN` in a workflow](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token)

## Final portrait direction

The current poor result should not be patched by adding more paths or accepting a noisy full-frame conversion. The reference succeeds because its portrait has been curated to a small tonal vocabulary at exactly the final display size. Henrik's portrait should be regenerated once from a crop that includes hair, face, neck, and a small amount of plain upper torso, while excluding the `StartNTNU` logo region entirely. Convert directly to a 25-row monospaced text target, preview it using the exact SVG font and spacing, then manually clean individual rows. That matches Andrew's actual delivery format while giving Henrik a portrait tailored to his source photo.
