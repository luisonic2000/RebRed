# 1.6-beta: optional Studio appearance

Select Appearance > Theme > RebRed Studio · Coral > Apply. Studio changes the entire workspace, not only colors. Other palette choices retain the classic workspace. Existing installations and new blank installs keep the previous default until Studio is explicitly selected.

Studio includes a charcoal/coral palette, creator toolbar with profile menu, two-line community rows, larger draft editor, two-column image gallery, collapsed personalization controls, collapsed validation/notes details and separate publication history. Community management, import/export, image selection, folder opening, clipboard, credits and draft checks remain available.

Live theme and language switches rebuild the workspace while preserving the active artist/community, edited title/body and selected files. Pane proportions are stored separately for classic and Studio layouts. Studio is implemented in App/studio_layout.py and reuses the existing planning logic.

Validation: 30 tests passed, including real Tk switching through Appearance, edited draft and selected-image preservation, language changes, collapsible details, restoring classic mode and saved Studio startup. A separate temporary-data preview launcher is App/tests/preview_studio.py. No user data is loaded by that preview.

Visual inspection via the Windows computer-use tool was attempted, but window approval timed out. Functional window tests passed; final visual assessment on the user's display is still needed. The mockup is a visual reference, not a pixel-exact native-widget specification.

Windows build: App/outputs/RebRed-1.6-beta.exe. Local JSON, personal profiles and backups are excluded from the executable and Git changes. Earlier unrelated roadmap items remain in PROGRESS-1.5.md.
