# 1.4-beta

Implemented:
- Creator toolbar above community/editor workspace.
- Collapsible draft options and corrected pane-ratio serialization.
- Drafts isolated by creator and community; preserved during switches, saved every ten seconds and on close.
- Official rule URL and review status editable in community settings; extra rule fields retained when saving.
- Source evidence and previous pack snapshot for seven communities: AnimeCommission, starvingartists, artcommissions, HungryArtists, DnD, DrawForMe, hireanartist.
- Corrected researched minima, links, DrawForMe paid-offer tag/weekend interval and title contact restrictions.
- DnD generation requests the author's own artwork description instead of supplying generated filler; validates 400-character requirement, title tags and warns about Eastern-time text-only Thursday. Promotion approval and Comm tag requirements are in notes.
- Additional live-check translations and visible last-post/next-release timestamps.
- Separate workspace, source evidence and dynamic translation modules.

Verification: 24 tests including real Tk draft switching, collapsed controls and appearance; syntax checks. Native clipboard, external drag behavior and crowded/scaled layouts still need interactive testing.

Research sources (accessed 2026-11-03):
- https://www.reddit.com/r/AnimeCommission/about/rules.json
- https://www.reddit.com/r/starvingartists/about/rules.json
- https://www.reddit.com/r/artcommissions/about/rules.json
- https://www.reddit.com/r/HungryArtists/about/rules.json
- https://www.reddit.com/r/DnD/wiki/rules/
- https://www.reddit.com/r/DrawForMe/about/rules.json
- https://www.reddit.com/r/hireanartist/about/rules.json

Sources are recorded as partial review, not a guarantee of exhaustive rule coverage. Remaining communities retain unverified status. The ArtistsforHire endpoint could not be fetched in this run.

Still pending: remaining community research; fully responsive layout at large text scales; complete translation of dialogs/dynamic messages; direct native external drag from thumbnails; further module extraction; version-independent Windows release workflow and public release. Current GitHub release workflow still refers to 1.2 and must not be used for this executable.

Adding a community: use Add, fill tags/prices/link policy, set the official URL and review date, and keep status unverified/partial until checked. Title/body templates accept existing brace tokens; preserve notes for constraints requiring manual inspection. Add pure-rule tests and a Tk interaction check for changed controls.
