# RebRed 1.2-beta

Local desktop planner for preparing commission posts manually on Windows and Linux. It does not sign in to Reddit, publish posts, create image copies, or automate browser actions. This clean beta has no creator information, links, or prices embedded in its post defaults. It starts with one blank artist profile. The Credits button is kept as a project credit.

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
- A searchable community list with an availability legend, plus a live Reddit title-length counter that warns when a title exceeds 300 characters.
- A less crowded draft toolbar that separates content settings from the primary prepare/open actions.
- Four dark appearance presets (Adwaita Dark, Catppuccin Mocha, Nord, and Dracula), an optional light palette, a custom accent color, text scaling, compact/comfortable density, and a reduced-motion preference. These preferences persist locally and recolor the whole interface using opaque semantic palettes.
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

Install Python 3.10 or newer and the dependencies. Windows includes Tkinter with standard Python distributions. On Debian/Ubuntu Linux, install `python3-tk` before the Python packages. From this folder, run:

```powershell
python -m pip install -r requirements.txt
python app.py
```

On Debian/Ubuntu, if Tkinter is not installed yet, run `sudo apt install python3-tk` first. The app creates its settings and history automatically: beside `app.py` on Windows, or in `$XDG_STATE_HOME/rebred` (default `~/.local/state/rebred`) on Linux. It never duplicates your image files and does not need a spreadsheet. Its data file is intentionally separate from files used by earlier personalized builds.

## Downloads

Download the latest release assets from [GitHub Releases](https://github.com/luisonic2000/RebRed/releases/latest):

- `RebRed-1.2-beta.exe` is the portable Windows x86-64 application.
- `RebRed-1.2-beta-x86_64.AppImage` is the Linux x86-64 application.
- `SHA256SUMS.txt` contains checksums for both downloads.

The Windows executable and Linux AppImage do not include personal profiles, posting history, or artwork. Windows stores `rebred_data.json` beside the executable; Linux stores it in `$XDG_STATE_HOME/rebred` or `~/.local/state/rebred`. Back up that file/folder separately when moving to another computer.

On Linux, make the AppImage executable if needed and launch it:

```bash
chmod +x RebRed-1.2-beta-x86_64.AppImage
./RebRed-1.2-beta-x86_64.AppImage
```

The AppImage targets x86-64 Linux and requires a graphical X11-compatible desktop (Wayland sessions can use XWayland). If the AppImage runtime cannot mount because FUSE is unavailable, install the distribution's FUSE 2 compatibility package or run it with `--appimage-extract-and-run`. Linux does not support copying image files to the clipboard from this app; open the image folder and drag files into the browser upload field.

To rebuild the one-file Windows executable from this folder:

```powershell
python -m pip install -r requirements.txt
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --distpath outputs --workpath build RebRed-1.2-beta.spec
```

Both release assets are built and attached automatically when a `v*` version tag is pushed. The Windows executable uses `RebRed-1.2-beta.spec`; the AppImage is built on Ubuntu 22.04 with PyInstaller and linuxdeploy.

The Tk interface uses opaque native widgets. Rounded custom widget corners and CSS-based styling are not available without replacing the interface toolkit, so RebRed keeps its existing lightweight Tk architecture instead.

## Important limits

The checks are an aid, not a promise that a subreddit or Reddit will accept a post. Rules change and the top-post study is not a substitute for the current community rules, so review the final draft before copying it to Reddit. The app deliberately does not automate Reddit submission, browser controls, account access, or bulk posting.
