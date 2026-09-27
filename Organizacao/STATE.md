# Current state

Last verified: 2026-09-27

Current source version: `1.0-beta`

Latest Windows delivery: `Finais/RebRed-1.0-beta/RebRed-1.0-beta.exe`

Public source repository: `https://github.com/luisonic2000/RebRed`

Verified locally:

- `python -m py_compile app.py`
- Headless posting-protection test harness
- Windows executable generated with PyInstaller in the previous delivery wave

Known limitation:

- The Tk graphical interface has not been exercised automatically. Manual user testing is still required for interaction and visual layout.

Next step:

- Run the headless suite from `Projeto/tests` before any functional change, then use a focused manual check for affected UI controls.
