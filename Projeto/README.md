# RebRed 1.0-beta

Local Windows planner for preparing commission posts manually. It does not sign in to Reddit, publish posts, create image copies, or automate browser actions. This clean beta has no creator information, links, or prices embedded in its post defaults. It starts with one blank artist profile. The Credits button is kept as a project credit.

## Open source and beta review

RebRed is released under the [MIT License](LICENSE). The application source, dependency list, and contribution guidance are included here so reviewers can inspect and test it before the public release. See [CONTRIBUTING.md](CONTRIBUTING.md) for the local setup and review scope.

## Included

- Separate profiles for each community, with their own image folder, posting interval, preferred days/times, draft library, allowed-link order, and rule checks.
- Separate creator profiles for you, a collaborator, or a client. Each one stores only the public handle, starting prices, and links the person chooses to add.
- A profile removal action with a confirmation step. The app keeps one blank profile available if the last profile is removed.
- VGen, ArtStation, Cara, Behance, website, Instagram, Bluesky, X, Twitch, YouTube, Discord, and Ko-fi fields. A community only shows filled links that its own allowed-link order permits.
- Each platform has separate public-link and @handle fields. Choose Link, @handle, or Both per platform. Portfolio entries always prioritize VGen, ArtStation, and Behance when that community allows them.
- Contact output is community-specific. Each starter profile has a conservative permitted-platform list, so a prohibited link or @handle is omitted from its draft rather than merely highlighted as a warning.
- Markdown or rich-text link formatting, optional starting prices, and optional restrained emoji placeholders.
- A community-aware title-tag checkbox. When a community requires a title tag such as `[For Hire]`, `[COM]`, or `[OC] [For Hire]`, the checkbox starts enabled and adds or removes that exact tag separately from the editable title. Communities without a required tag keep it unavailable.
- A required starting price is locked on when a community requires it in the post body. r/starvingartists now requires `[For Hire]`, a public portfolio, a starting price, and uses a seven-day local repost interval.
- Six content types: Anime, Comic, Cartoon, Realistic, Splash art, and Animation. Each includes fifteen editable starting directions for titles and bodies, so a comic draft never starts from an anime-specific title.
- Starter profiles for 33 Reddit communities, embedded directly in the program with their own schedule, folder, draft library, link order, and editable rule pack. The app does not need `Horários.ods` or any other spreadsheet to run. Commission-focused additions include DrawForMe, artistforhire, hireanartist, and VGen.
- Communities that do not accept commission ads use an `Artwork / OC` route. Their prepared drafts remove the commission pitch, price, portfolio links, and contact call-to-action instead of producing a misleading `For Hire` post.
- Live checks for title terms, @handle, price minimums, portfolio/social links, forbidden links, selected image reuse, and the local posting interval.
- A 1–9 image selector for each prepared draft. It controls both the random selection and the maximum manual selection in the image list.
- A `Choose image folder` action on the main screen. It lets you choose the exact folder for that community, shows a thumbnail of the selected image, and can open that selected folder in Explorer. Select one or more images and use `Copy selected images` (or Ctrl+C while the list has focus) to place the existing files on the Windows clipboard for a manual Ctrl+V into a compatible browser upload field. It never creates, copies, or uploads image files.
- Three editable suggested Brasília-time windows are stored for every allowed weekday. Live availability colors are pastel green for a configured window, yellow for a suitable day outside that window, and red for other days. The community list refreshes once per minute and places green communities first.
- The main work area has two drag dividers: one adjusts the draft versus image workspace, and another adjusts that workspace versus the rule checks and community notes.
- After `Mark as posted`, the local time is saved. A community with an active repost interval is shown in pastel brown, its `Mark as posted` button is disabled, and it becomes available only after its configured interval expires.
- A persistent footer notice now states the locally recorded “do not publish until” time. Draft preparation remains available during the interval, but the community remains brown and the live rule check warns against publishing it. Recording a post always activates a lock: the community rule interval when configured, otherwise a conservative local 24-hour lock.
- Save, import/export, and copy-to-another-community controls. Copying preserves the destination's image folder and draft library while copying the rule, timing, and allowed-link settings.
- Clipboard buttons for the title and body, plus a local `Mark as posted` history entry. The user publishes manually.
- `Open community` beside `Prepare a draft` opens the selected subreddit in the default browser without signing in, posting, or uploading anything.
- Import/export of community templates. Templates contain settings only, never artwork or posting history.

## Run locally

Windows already includes the Tk interface used by this app. From this folder, run:

```powershell
python app.py
```

The app creates `rebred_data.json` beside `app.py` to remember its settings and history. It never duplicates your image files. This configuration file is created automatically and is not a spreadsheet dependency. It is intentionally separate from the data file used by earlier personalized builds.

## Portable EXE

The portable EXE is in `outputs`. Keep `rebred_data.json` beside it if you move the program to another computer. RebRed includes its starter communities and rules internally; no spreadsheet needs to travel with it.

## Important limits

The checks are an aid, not a promise that a subreddit or Reddit will accept a post. Rules change and the top-post study is not a substitute for the current community rules, so review the final draft before copying it to Reddit. The app deliberately does not automate Reddit submission, browser controls, account access, or bulk posting.
