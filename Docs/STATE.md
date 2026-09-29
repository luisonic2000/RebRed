# Current state

Last verified: 2026-09-28

Current source version: `1.2-beta`

Latest Windows delivery: `App/outputs/RebRed-1.2-beta.exe`

Linux AppImages and Windows release executables are built and attached to GitHub Releases by `.github/workflows/release.yml` when a `v*` tag is pushed.

Current preview work includes persisted appearance presets and accessible text scaling. Platform downloads are published after the Windows and Linux release workflows both pass.

Public source repository: `https://github.com/luisonic2000/RebRed`

Verified locally for 1.2-beta:

- `python -m unittest discover -s App\tests -v` — 14 tests passed, including a real Tk appearance-dialog check using a temporary data file.
- `python -m py_compile App\app.py App\tests\test_appearance.py App\tests\test_appearance_ui.py App\tests\test_posting_lock.py App\tests\test_ui_helpers.py`
- The Windows 1.2-beta executable starts in an isolated temporary directory without accessing the user's profile.
- `git diff --check` reports no whitespace errors.

Known limitations:

- Manual user testing is still recommended for image selection, clipboard file paste, dialogs, and browser opening.
- Reddit community rules can change; built-in checks remain guidance only.

Release status:

- The 1.2-beta Windows executable is built locally at `App/outputs/RebRed-1.2-beta.exe`.
- The Linux AppImage and public 1.2-beta release have not been built or published; the release workflow builds and publishes both platforms after a `v*` tag is pushed.
