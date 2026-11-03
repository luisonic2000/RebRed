# 1.3-beta implementation progress

Implemented: atomic JSON replacement, validated previous-version recovery, separate storage and rule helper modules, unresolved-token detection and copy protection, generated portfolio/social filtering against banned domains, manual-edit replacement confirmation, import preview confirmation, publication undo, availability labels, validation summary, persisted pane proportions with reset, selected-image thumbnails and internal drag ordering.

Remaining from the requested full redesign: official source verification for all community packs and individual restriction evidence; complete rule editor provenance controls; complete translation of dynamic messages; top profile toolbar; collapsible advanced controls; responsive wrapping for small screens; save/restore drafts across communities; external native file dragging; further module extraction; automated publishing/release preparation.

Existing dates in built-in packs do not establish verification. Packs without explicit verified status now request review. Suggested engagement windows are estimates.

The generated executable is a clean build: the build embeds application modules only, not local JSON profiles or recovery files. Preserve the existing rebred_data.json beside an updated executable when retaining portable Windows data.

Manual checks still required: nine thumbnails on a small display, internal reordering, clipboard paste in target browsers, recovery dialog, and panel proportions after reopening.
