"""Optional Studio workspace; uses the same planner actions and data."""
import tkinter as tk
from tkinter import ttk
from scroll_workspace import ScrollWorkspace


class CommunityCards(ttk.Treeview):
    """Two-line community rows with the existing planner list interface."""
    def __init__(self, parent):
        super().__init__(parent, show="tree", selectmode="browse", style="Studio.Treeview")
        self.column("#0", width=225, minwidth=180, stretch=True)

    def insert(self, position, text):
        name, _, state = text.partition(" · ")
        return super().insert("", "end", text=f"r/{name}\n{state}")

    def delete(self, *args):
        children = self.get_children()
        if children:
            super().delete(*children)

    def itemconfig(self, index, **options):
        tag = f"community-{index}"
        self.tag_configure(tag, **options)
        self.item(self.get_children()[index], tags=(tag,))

    def selection_set(self, index):
        super().selection_set(self.get_children()[index])

    def curselection(self):
        children = self.get_children()
        return tuple(children.index(item) for item in self.selection() if item in children)

    def see(self, index):
        super().see(self.get_children()[index])

    def size(self):
        return len(self.get_children())

    def bind(self, sequence=None, func=None, add=None):
        if sequence == "<<ListboxSelect>>":
            super().bind("<ButtonRelease-1>", func, add)
            super().bind("<KeyRelease-Up>", func, add)
            return super().bind("<KeyRelease-Down>", func, add)
        return super().bind(sequence, func, add)


def build_studio(app):
    app.outer_frame = ttk.Frame(app, padding=16)
    app.outer_frame.pack(fill="both", expand=True)
    app.outer_frame.columnconfigure(1, weight=1)
    app.outer_frame.columnconfigure(0, minsize=245)
    app.outer_frame.rowconfigure(1, weight=1)

    top = ttk.Frame(app.outer_frame, padding=(4, 0, 4, 14))
    top.grid(row=0, column=0, columnspan=2, sticky="ew")
    ttk.Label(top, text="◢ RebRed", font=app.ui_font(20, "bold")).pack(side="left", padx=(0, 28))
    ttk.Label(top, text="Creator profile", style="Status.TLabel").pack(side="left", padx=(0, 8))
    app.creator_combo = ttk.Combobox(top, state="readonly", width=22)
    app.creator_combo.pack(side="left")
    app.creator_combo.bind("<<ComboboxSelected>>", app.on_creator_select)
    menu = tk.Menu(top, tearoff=False)
    for text, action in (("Add", app.add_creator), ("Edit", app.edit_creator), ("Remove profile", app.remove_creator), ("Export", app.export_creator), ("Import creator template", app.import_creator)):
        menu.add_command(label=app.tr(text), command=action)
    tools = ttk.Menubutton(top, text="⋯", menu=menu, width=3)
    tools.pack(side="left", padx=6)
    app.language_button = ttk.Button(top, command=app.toggle_ui_language, width=9)
    app.language_button.pack(side="right")
    app.appearance_button = ttk.Button(top, command=app.open_appearance)
    app.appearance_button.pack(side="right", padx=8)

    sidebar = ttk.Frame(app.outer_frame, padding=(0, 12, 16, 0))
    sidebar.grid(row=1, column=0, sticky="nsew")
    ttk.Label(sidebar, text="Communities", font=app.ui_font(16, "bold")).pack(anchor="w", pady=(0, 15))
    search = ttk.Entry(sidebar, textvariable=app.community_search_var, width=24)
    search.pack(fill="x", pady=(0, 7))
    ttk.Label(sidebar, text="Search communities", style="Status.TLabel").pack(anchor="w")
    ttk.Label(sidebar, textvariable=app.community_count_var, style="Status.TLabel").pack(anchor="w", pady=(2, 12))
    app.profile_list = CommunityCards(sidebar)
    app.profile_list.pack(fill="both", expand=True)
    app.profile_list.bind("<<ListboxSelect>>", app.on_profile_select)
    communities_menu = tk.Menu(sidebar, tearoff=False)
    for text, action in (("Add", app.add_profile), ("Edit", app.edit_profile), ("Remove", app.remove_profile), ("Export community template", app.export_profile), ("Import community template", app.import_profile), ("Copy settings to…", app.copy_community_settings)):
        communities_menu.add_command(label=app.tr(text), command=action)
    communities_menu.add_separator()
    communities_menu.add_command(label=app.tr("Restore layout"), command=app.reset_layout)
    ttk.Menubutton(sidebar, text="Manage communities", menu=communities_menu).pack(fill="x", pady=(12, 6))
    ttk.Button(sidebar, text="Credits", command=app.open_credits).pack(anchor="w")

    app.workspace_scroll = ScrollWorkspace(app.outer_frame)
    app.workspace_scroll.grid(row=1, column=1, sticky="nsew")
    main = app.workspace_scroll.content
    head = ttk.Frame(main, padding=(12, 5, 12, 14))
    head.pack(fill="x")
    app.community_heading = ttk.Label(head, font=app.ui_font(24, "bold"))
    app.community_heading.pack(side="left")
    app.open_community_button = ttk.Button(head, text="Open community", command=app.open_community)
    app.open_community_button.pack(side="right")
    ttk.Label(main, text="Prepare your next post", style="Status.TLabel").pack(anchor="w", padx=12)

    controls = ttk.Frame(main, padding=12)
    controls.pack(fill="x", pady=(8, 5))
    category = ttk.Combobox(controls, textvariable=app.category_var, values=["Anime", "Comic", "Cartoon", "Realistic", "Splash art", "Animation"], width=14, state="readonly")
    category.pack(side="left", padx=(0, 8))
    post = ttk.Combobox(controls, textvariable=app.post_type_var, values=["For Hire", "Hiring", "Artwork / OC", "Portfolio Review", "Meta"], width=15, state="readonly")
    post.pack(side="left", padx=(0, 8))
    for widget in (category, post):
        widget.bind("<<ComboboxSelected>>", lambda event: app.validate())
    app.advanced_visible = tk.BooleanVar(value=False)
    ttk.Checkbutton(controls, text="Customize draft", variable=app.advanced_visible, command=app.toggle_studio_options).pack(side="left")
    app.prepare_button = ttk.Button(controls, text="Prepare a draft", style="Accent.TButton", command=app.prepare_draft)
    app.prepare_button.pack(side="right")
    app.advanced_options = ttk.Frame(main, padding=12)
    links = ttk.Combobox(app.advanced_options, textvariable=app.link_style_var, values=["Markdown", "Rich text"], width=13, state="readonly")
    links.grid(row=0, column=0, padx=(0, 10))
    app.include_price_check = ttk.Checkbutton(app.advanced_options, text="Include starting price", variable=app.include_price_var, command=app.validate)
    app.include_price_check.grid(row=0, column=1, sticky="w")
    app.title_tag_check = ttk.Checkbutton(app.advanced_options, variable=app.title_tag_var, command=app.on_title_tag_toggle)
    app.title_tag_check.grid(row=1, column=1, sticky="w")
    ttk.Checkbutton(app.advanced_options, text="Commercial use / budget", variable=app.commercial_var, command=app.validate).grid(row=1, column=0, sticky="w")

    editor = ttk.PanedWindow(main, orient="horizontal")
    editor.pack(fill="both", expand=True, padx=12, pady=10)
    app.studio_editor = editor
    draft = ttk.Frame(editor, padding=(0, 0, 18, 0))
    editor.add(draft, weight=3)
    draft.columnconfigure(0, weight=1)
    draft.rowconfigure(3, weight=1)
    ttk.Label(draft, text="Your draft", font=app.ui_font(16, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 14))
    app.title_count_label = ttk.Label(draft, textvariable=app.title_count_var, style="Counter.TLabel")
    app.title_count_label.grid(row=0, column=1, sticky="e")
    ttk.Label(draft, text="Title", style="Status.TLabel").grid(row=1, column=0, sticky="w", pady=(0, 6))
    app.title_entry = ttk.Entry(draft, font=app.ui_font(11))
    app.title_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 18))
    app.body_text = tk.Text(draft, height=15, width=40, wrap="word", padx=16, pady=16, relief="flat", font=app.ui_font(11), undo=True)
    app.body_text.grid(row=3, column=0, columnspan=2, sticky="nsew")
    app.body_count_label = ttk.Label(draft, textvariable=app.body_count_var, style="Counter.TLabel")
    app.body_count_label.grid(row=4, column=1, sticky="e", pady=5)
    buttons = ttk.Frame(draft)
    buttons.grid(row=5, column=0, columnspan=2, sticky="w", pady=8)
    ttk.Button(buttons, text="Copy title", command=lambda: app.copy_text(app.title_entry.get(), app.tr("Title copied."))).pack(side="left", padx=(0, 8))
    ttk.Button(buttons, text="Copy body", command=lambda: app.copy_text(app.body_text.get("1.0", "end").strip(), app.tr("Body copied."))).pack(side="left")
    for widget in (app.title_entry, app.body_text):
        widget.bind("<KeyRelease>", lambda event: app.validate())

    images = ttk.Frame(editor, padding=(16, 0, 0, 0))
    editor.add(images, weight=2)
    ttk.Label(images, text="Selected images", font=app.ui_font(16, "bold")).pack(anchor="w", pady=(0, 14))
    app.folder_label = ttk.Label(images, wraplength=320, style="Status.TLabel")
    app.folder_label.pack(fill="x", pady=(0, 6))
    image_toolbar = ttk.Frame(images)
    image_toolbar.pack(fill="x", pady=(0, 8))
    ttk.Button(image_toolbar, text="Choose image folder…", command=app.choose_image_folder).pack(side="left")
    ttk.Button(image_toolbar, text="↗", command=app.open_folder, width=3).pack(side="left", padx=4)
    count = ttk.Combobox(image_toolbar, textvariable=app.image_count_var, values=list(range(1, 10)), state="readonly", width=3)
    count.pack(side="right")
    count.bind("<<ComboboxSelected>>", app.on_image_count_changed)
    app.image_grid = ttk.Frame(images)
    app.image_grid.pack(fill="both", expand=True)
    app._grid_photos = []
    app.image_list = tk.Listbox(images, selectmode="extended", exportselection=False, height=5)
    app.image_list.bind("<<ListboxSelect>>", app.on_image_select)
    app.image_list.bind("<Control-c>", app.copy_selected_images)
    ttk.Button(images, text="Choose images", command=app.toggle_studio_file_list).pack(anchor="w", pady=4)
    ttk.Label(images, text="Drag to reorder or send files", style="Status.TLabel").pack(anchor="w", pady=5)
    ttk.Button(images, text="Copy selected images", command=app.copy_selected_images).pack(fill="x", pady=5)
    app.thumbnail_label = ttk.Label(images)
    app.thumbnail_name = ttk.Label(images)
    app.thumbnail_image = None

    status = ttk.Frame(main, padding=12)
    status.pack(fill="x", padx=12, pady=(4, 8))
    app.validation_summary_var = tk.StringVar()
    ttk.Label(status, textvariable=app.validation_summary_var, font=app.ui_font(11, "bold")).pack(side="left")
    ttk.Button(status, text="View details", command=app.toggle_studio_details).pack(side="right")
    details = ttk.PanedWindow(main, orient="horizontal")
    app.studio_details = details
    app.validation_text = tk.Text(details, height=7, width=40, wrap="word", state="disabled")
    details.add(app.validation_text, weight=3)
    app.notes_label = ttk.Label(details, wraplength=320, justify="left")
    details.add(app.notes_label, weight=2)
    app.workspace_panes = {"studio-editor": editor, "studio-details": details}
    app.after(250, app.restore_layout)
    footer = ttk.Frame(main, padding=12)
    footer.pack(fill="x", padx=12)
    app.repost_notice_label = ttk.Label(footer, textvariable=app.repost_notice_var, wraplength=430, style="Status.TLabel")
    app.repost_notice_label.pack(side="left", fill="x", expand=True)
    app.mark_posted_button = ttk.Button(footer, text="Mark as posted", command=app.mark_posted)
    app.mark_posted_button.pack(side="right")
    extra = ttk.Frame(main, padding=12)
    extra.pack(fill="x")
    ttk.Button(extra, text="Undo last publication", command=app.undo_last_post).pack(side="right")
    ttk.Button(extra, text="Save community settings", command=app.save_community_settings).pack(side="right", padx=6)
    ttk.Label(extra, text="RebRed Studio · Brasília (UTC−3)", style="Status.TLabel").pack(side="left")


def toggle_options(app):
    if app.advanced_visible.get():
        app.advanced_options.pack(fill="x", before=app.studio_editor, padx=12)
    else:
        app.advanced_options.pack_forget()


def toggle_details(app):
    if app.studio_details.winfo_manager():
        app.studio_details.pack_forget()
    else:
        app.studio_details.pack(fill="x", after=app.studio_editor, padx=12)
