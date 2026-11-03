# Current state

Last verified: 2026-11-03

Current source: 1.5-beta. Windows delivery: App/outputs/RebRed-1.5-beta.exe.

Repository: https://github.com/luisonic2000/RebRed

Working branch: feat/reliability-layout-1.3. Main is not automatically merged.

Current progress and manual checklist: PROGRESS-1.5.md. Prior incremental work is recorded in PROGRESS-1.3.md and PROGRESS-1.4.md.

27 tests passed, including actual Tk windows with temporary data, Windows file data-object creation, storage recovery and rule migrations. Syntax checks passed. The executable embeds no local JSON or profiles.

Release workflow now targets Windows and builds independently of version-specific specs. GitHub CI and public release publication have not yet been verified; no tag was pushed.

Remaining work: interactive drag-and-drop testing in browsers, full dialog translations, remaining community source research, additional code modularization and more refined responsive layouts. Seventeen packs have partial source reviews, not exhaustive verification. Suggested engagement windows remain estimates.
