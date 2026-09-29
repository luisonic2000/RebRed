# Decisions

## 2026-09-27: Mandatory local lock after recording a post

When a community has a configured repost interval, RebRed uses it. When it does not, RebRed applies a 24-hour local lock after `Mark as posted`.

Reason: recording a post must visibly override an otherwise green posting window and reduce accidental immediate reposting. Draft preparation stays enabled because it does not publish anything.

## 2026-09-27: Community-specific contact policy

Each starter community has its own permitted platform list. VGen, ArtStation, and Behance are preferred portfolio ordering when allowed. A creator may choose link, @handle, or both for a platform, but a platform not permitted by the community is omitted.
