# Test harness

Run headless tests from `App`:

```powershell
python -m unittest discover -s tests -v
```

The harness imports the application module without creating a Tk window. It uses a small fake planner and in-memory history only. It does not access the browser, Reddit, image folders, clipboard, network, hardware, or an executable build.

Run a syntax check separately:

```powershell
python -m py_compile app.py
```

Manual checks remain necessary for Tk layout, clipboard file paste behavior, folder dialogs, and default-browser opening.
