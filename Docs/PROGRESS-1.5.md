# 1.5-beta

Implemented:
- Scrollable editor workspace and wrapped creator actions preserve access at 800x560. This is an accessibility fallback, not a complete responsive redesign.
- Native Windows Shell drag offers existing selected files with copy-only effect. Drag inside the thumbnail grid to reorder; move outside the grid while holding the left button to offer files to external applications. Escape cancels. Destination support varies.
- Added pywin32 as a conditional Windows dependency; verified a real CF_HDROP object without performing an external upload.
- Translated additional live check messages and status text; distinguished suggested windows from interval locks.
- Windows-only release workflow now builds from app.py without a version-pinned spec, runs tests, computes SHA256 and uploads artifacts. Tagged builds publish a prerelease. No release tag was pushed in this implementation.
- Expanded source-backed partial rule records from seven to seventeen communities. Added ComicBookCollabs, VGen, commissions, artcommission, ArtSale, ArtStore, commissionart, gameDevClassifieds, gameDevJobs and INAT.
- ComicBookCollabs and VGen require manually written text due to explicit bans on generated text. gameDevJobs requires a game-development offer rather than personal commissions. ArtSale commission tag corrected, and INAT word-count recommendation displayed.

Research performed 2026-11-03 using the communities' official /about/rules.json endpoints. These remain partial reviews: sidebar, wiki, pinned posts and moderator discretion can add conditions. artistforhire returned an empty structured rule list and was left unverified. comissions and Commissions_rh could not be fetched. DnDart and dndcommissions were inspected but their incomplete excerpt did not support changing the pack in this pass.

Validation: 27 tests passed including real Tk small-window scrolling, draft preservation, dynamic translations, recovery and Windows CF_HDROP creation. Syntax checks passed. Native drag must still be checked interactively with the intended browser and nine images; complete UI translation and the remaining community research are pending. CI workflow changes have not run on GitHub yet.

Manual checklist:
1. Open at 800x560 and with 130% text scaling; scroll to every control.
2. Select 1 and 9 images, reorder inside the grid, copy and paste into an upload field.
3. Drag outside the grid into the browser file-upload area; cancel with Escape and retry.
4. Switch artist and subreddit and reopen to check drafts and layout.
5. Review the rules source and acknowledge manual requirements before posting.

No user profile, local settings, images or backups are embedded in the executable.

Native drag references: https://learn.microsoft.com/en-us/windows/win32/api/shlobj_core/nf-shlobj_core-shcreatedataobject and https://raw.githubusercontent.com/mhammond/pywin32/main/com/win32com/src/extensions/PyIDropSource.cpp . Only copy effects are offered.
