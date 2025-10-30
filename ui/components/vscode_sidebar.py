import tkinter as tk
import ttkbootstrap as ttk
from ui.components.modern_theme import ModernTheme
import os
from tkinter import messagebox

class VSCodeSidebar:
    def __init__(self, parent, db_manager, ai_integration):
        self.parent = parent
        self.db_manager = db_manager
        self.ai_integration = ai_integration
        self.theme = ModernTheme()
        self.is_collapsed = False
        # Tabs: DB, TRIGGER, VIEW, FUNCTION, INDEX, PROCEDURE
        self.tabs = [
            {"key": "dbafdcaf", "icon": "🗄️", "label": "DB"},
            {"key": "trigger", "icon": "⚡", "label": "TRIGGER"},
            {"key": "view", "icon": "👁️", "label": "VIEW"},
            {"key": "function", "icon": "ƒ", "label": "FUNCTION"},
            {"key": "index", "icon": "🔍", "label": "INDEX"},
            {"key": "procedure", "icon": "⚙️", "label": "PROCEDURE"},
        ]
        self.active_tab_key = None
        self.panel_frames = {}
        self.create_widgets()
        
    def create_widgets(self):
        """Create the horizontal-tab style sidebar with full-area panels."""
        # Main sidebar frame
        self.sidebar_frame = ttk.Frame(self.parent, style="SideNav.TFrame", width=300)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
        self.sidebar_frame.pack_propagate(False)
        
        # Top horizontal icon-only tab bar
        self.create_tab_bar()

        # Content container (fills the rest)
        self.content_container = ttk.Frame(self.sidebar_frame, style="SideNav.TFrame")
        self.content_container.pack(fill="both", expand=True, padx=6, pady=6)

        # Default empty state
        self.empty_state = ttk.Frame(self.content_container, style="SideNav.TFrame")
        self.empty_state.pack(fill="both", expand=True)
        empty_label = ttk.Label(
            self.empty_state,
            text="Select a tab",
            font=("Segoe UI", 11, "bold"),
            foreground="#1a1a1a"
        )
        empty_label.pack(expand=True)
        
        # Collapse/expand button
        self.create_collapse_button()
        
    def create_tab_bar(self):
        """Create the horizontal emoji tab bar."""
        tabbar = ttk.Frame(self.sidebar_frame, style="SideNav.TFrame")
        tabbar.pack(fill=tk.X, padx=8, pady=8)

        self._tab_buttons = {}

        for tab in self.tabs:
            btn = tk.Label(
                tabbar,
                text=tab["icon"],
                bg="#ffffff",  # white background
                fg="#333333",
                bd=0,
                font=("Segoe UI Emoji", 14, "normal"),
                width=2,
                height=1,
                relief="flat",
            )
            btn.pack(side=tk.LEFT, padx=6)
            btn.bind("<Button-1>", lambda e, key=tab["key"]: self.switch_tab(key))
            btn.bind("<Enter>", lambda e, b=btn: b.config(fg="#0066CC"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(fg="#333333" if b.cget("bg") == "#ffffff" else "#ffffff"))
            self._tab_buttons[tab["key"]] = btn

    def _update_active_tab_styles(self):
        for key, btn in self._tab_buttons.items():
            if key == self.active_tab_key:
                btn.config(bg="#FFA500", fg="#000000", font=("Segoe UI Emoji", 14, "bold"))
            else:
                btn.config(bg="#ffffff", fg="#333333", font=("Segoe UI Emoji", 14, "normal"))
    
    def switch_tab(self, tab_key):
        """Switch to the selected tab, rendering its panel full-area."""
        if tab_key == self.active_tab_key:
            return

        # Clear current content
        for child in self.content_container.winfo_children():
            child.pack_forget()

        self.active_tab_key = tab_key
        self._update_active_tab_styles()

        if tab_key not in self.panel_frames:
            if tab_key == "db":
                self.panel_frames[tab_key] = self._create_db_panel(self.content_container)
            elif tab_key == "trigger":
                self.panel_frames[tab_key] = self._create_list_panel(self.content_container, "Triggers")
            elif tab_key == "view":
                self.panel_frames[tab_key] = self._create_list_panel(self.content_container, "Views")
            elif tab_key == "function":
                self.panel_frames[tab_key] = self._create_list_panel(self.content_container, "Functions")
            elif tab_key == "index":
                self.panel_frames[tab_key] = self._create_list_panel(self.content_container, "Indexes")
            elif tab_key == "procedure":
                self.panel_frames[tab_key] = self._create_list_panel(self.content_container, "Procedures")

        panel = self.panel_frames.get(tab_key)
        if panel is not None:
            panel.pack(fill="both", expand=True)
        else:
            # Fallback to empty state
            self.empty_state.pack(fill="both", expand=True)
    
    def _create_search_bar(self, parent, placeholder="Search..."):
        wrapper = ttk.Frame(parent)
        wrapper.pack(fill=tk.X, pady=4)
        entry = ttk.Entry(wrapper)
        entry.insert(0, placeholder)
        def _on_focus_in(_):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
        def _on_focus_out(_):
            if not entry.get():
                entry.insert(0, placeholder)
        entry.bind("<FocusIn>", _on_focus_in)
        entry.bind("<FocusOut>", _on_focus_out)
        entry.pack(fill=tk.X)
        return entry
    
    def _create_db_panel(self, parent):
        panel = ttk.Frame(parent, style="SideNav.TFrame")

        # Search bar
        search = self._create_search_bar(panel, "Search…")

        # Tree area + optional data preview split
        split = ttk.PanedWindow(panel, orient=tk.VERTICAL)
        split.pack(fill=tk.BOTH, expand=True)

        tree_frame = ttk.Frame(split, style="SideNav.TFrame")
        preview_frame = ttk.Frame(split, style="SideNav.TFrame")

        # TreeView
        columns = ("type", "details")
        tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse")
        tree.pack(fill=tk.BOTH, expand=True)

        self.db_tree = tree
        self.db_preview = preview_frame
        self.db_search_entry = search

        # Bindings
        tree.bind("<Double-1>", self._on_db_tree_double_click)
        tree.bind("<Button-3>", self._on_db_tree_right_click)
        search.bind("<KeyRelease>", self._on_db_search_change)

        # Initial populate
        self._populate_db_tree()

        split.add(tree_frame, weight=3)
        split.add(preview_frame, weight=2)

        return panel
    
    def _populate_db_tree(self):
        if not hasattr(self, "db_tree"):
            return
        tree = self.db_tree
        for item in tree.get_children():
            tree.delete(item)

        current = self.db_manager.current_db if hasattr(self.db_manager, "current_db") else None
        root_label = f"postgres (connected)" if current else "No database selected"
        root = tree.insert("", "end", text=f"{root_label}")

        if not current:
            return

        # Example structure: schema -> Tables/Views/Functions -> table -> columns/Constraints/Indexes/Triggers
        schema_node = tree.insert(root, "end", text="public")
        tables_node = tree.insert(schema_node, "end", text="Tables")

        try:
            tables = self.db_manager.get_tables() if hasattr(self.db_manager, "get_tables") else []
        except Exception:
            tables = []

        for table in tables:
            t_node = tree.insert(tables_node, "end", text=table)
            # Columns
            cols_parent = tree.insert(t_node, "end", text="Columns")
            try:
                columns = self.db_manager.get_columns(table) if hasattr(self.db_manager, "get_columns") else []
            except Exception:
                columns = []
            for col in columns:
                # Expect dict with name, type, pk, fk, not_null, default
                name = col.get("name", "col")
                ctype = col.get("type", "")
                flags = []
                if col.get("pk"): flags.append("PK")
                if col.get("fk"): flags.append("FK")
                if col.get("not_null"): flags.append("NN")
                if col.get("default") is not None: flags.append("DEF")
                meta = (" ".join(flags)).strip()
                label = f"{name}    {ctype} {meta}".rstrip()
                tree.insert(cols_parent, "end", text=label)

            # Subnodes
            tree.insert(t_node, "end", text="Constraints")
            tree.insert(t_node, "end", text="Indexes")
            tree.insert(t_node, "end", text="Triggers")

        # Views, Functions
        tree.insert(schema_node, "end", text="Views")
        tree.insert(schema_node, "end", text="Functions")
    
    def _on_db_search_change(self, event=None):
        query = (self.db_search_entry.get() or "").strip().lower()
        if not query:
            self._populate_db_tree()
            return
        # Simple filter: rebuild tree with only matching table/column names
        tree = self.db_tree
        for item in tree.get_children():
            tree.delete(item)

        current = self.db_manager.current_db if hasattr(self.db_manager, "current_db") else None
        root_label = f"postgres (connected)" if current else "No database selected"
        root = tree.insert("", "end", text=f"{root_label}")
        if not current:
            return
        schema_node = tree.insert(root, "end", text="public")
        tables_node = tree.insert(schema_node, "end", text="Tables")
        try:
            tables = self.db_manager.get_tables() if hasattr(self.db_manager, "get_tables") else []
        except Exception:
            tables = []
        for table in tables:
            if query in table.lower():
                tree.insert(tables_node, "end", text=table)
                continue
            try:
                columns = self.db_manager.get_columns(table) if hasattr(self.db_manager, "get_columns") else []
            except Exception:
                columns = []
            match_cols = [c for c in columns if query in c.get("name", "").lower()]
            if match_cols:
                t_node = tree.insert(tables_node, "end", text=table)
                cols_parent = tree.insert(t_node, "end", text="Columns")
                for col in match_cols:
                    name = col.get("name", "col")
                    ctype = col.get("type", "")
                    tree.insert(cols_parent, "end", text=f"{name}    {ctype}")
    
    def create_collapse_button(self):
        """Create the collapse/expand button."""
        collapse_frame = ttk.Frame(self.sidebar_frame, style="SideNav.TFrame")
        collapse_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=8)
        
        self.collapse_button = tk.Button(collapse_frame, text="◀", 
                                        command=self.toggle_collapse,
                                        bg="#ffffff", fg="#333333", bd=0,
                                        font=("Segoe UI", 10), width=3, height=1,
                                        activebackground="#E6F3FF", activeforeground="#000000")
        self.collapse_button.pack(fill=tk.X)
        
    def toggle_collapse(self):
        """Toggle the sidebar collapse state."""
        if self.is_collapsed:
            self.sidebar_frame.configure(width=300)
            self.collapse_button.configure(text="◀")
            self.is_collapsed = False
        else:
            self.sidebar_frame.configure(width=50)
            self.collapse_button.configure(text="▶")
            self.is_collapsed = True
    # Context menu and actions for DB panel
    def _on_db_tree_right_click(self, event):
        menu = tk.Menu(self.parent, tearoff=0)
        menu.add_command(label="View Data", command=self._action_view_data)
        menu.add_command(label="Edit", command=self._action_edit)
        menu.add_command(label="Generate SQL", command=self._action_generate_sql)
        menu.add_command(label="Script CREATE", command=self._action_script_create)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _on_db_tree_double_click(self, event):
        # Show simple data preview for tables
        sel = self.db_tree.selection()
        if not sel:
            return
        node_text = self.db_tree.item(sel[0]).get("text", "")
        parent = self.db_tree.parent(sel[0])
        if parent:
            parent_text = self.db_tree.item(parent).get("text", "")
            is_table = self.db_tree.item(parent).get("text", "") != "Columns" and parent_text and parent_text != "Tables" and node_text and parent_text == "Tables"
        else:
            is_table = False

        # Detect table node (child of Tables)
        if self.db_tree.item(sel[0]).get("text", "") and self.db_tree.item(self.db_tree.parent(sel[0])).get("text", "") == "Tables":
            table_name = node_text
            self._show_table_preview(table_name)

    def _show_table_preview(self, table_name):
        frame = self.db_preview
        for c in frame.winfo_children():
            c.destroy()
        label = ttk.Label(frame, text=f"Preview: {table_name}", font=("Segoe UI", 10, "bold"))
        label.pack(anchor=tk.W, padx=6, pady=4)
        text = tk.Text(frame, height=8, bg="#E6F3FF", fg="#1a1a1a", bd=0)
        text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        try:
            rows = []
            if hasattr(self.db_manager, "preview_table"):
                rows = self.db_manager.preview_table(table_name)
            elif hasattr(self.db_manager, "fetch_preview"):
                rows = self.db_manager.fetch_preview(table_name)
                    else:
                rows = []
            for r in rows[:50]:
                text.insert(tk.END, f"{r}\n")
        except Exception as e:
            text.insert(tk.END, f"Error previewing table: {e}")

    # Placeholder context actions
    def _action_view_data(self):
        messagebox.showinfo("View Data", "Opening data preview…")

    def _action_edit(self):
        messagebox.showinfo("Edit", "Open editor for selected object…")

    def _action_generate_sql(self):
        messagebox.showinfo("Generate SQL", "Generating SQL…")

    def _action_script_create(self):
        messagebox.showinfo("Script CREATE", "Creating CREATE script…")

    # Generic list panels for other tabs
    def _create_list_panel(self, parent, title):
        panel = ttk.Frame(parent, style="SideNav.TFrame")
        search = self._create_search_bar(panel, f"Search {title}…")
        listbox = tk.Listbox(panel, bd=0, highlightthickness=0)
        listbox.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        listbox.insert(tk.END, f"No items. Connect to a database.")
        return panel
