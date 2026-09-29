# Current state

Last verified: 2026-09-28

Current source version: `1.1-beta`

Latest Windows delivery: `Projeto/outputs/RebRed-1.1-beta.exe`

Public source repository: `https://github.com/luisonic2000/RebRed`

Verified locally:

- `python -m py_compile app.py`
- Headless tests for posting protection, community search, and title length
- Tk window smoke check at compact Windows window sizes

Known limitations:

- Manual user testing is still recommended for image selection, clipboard file paste, dialogs, and browser opening.
- Reddit community rules can change; built-in checks remain guidance only.

Next step:

- Run the headless suite from `Projeto/tests` and rebuild the portable EXE when releasing source changes.
