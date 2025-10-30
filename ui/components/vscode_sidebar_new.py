import tkinter as tk
import ttkbootstrap as ttk
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ui.components.modern_theme import ModernTheme
from tkinter import messagebox

class VSCodeSidebar:
    def __init__(self, parent, db_manager, ai_integration):
        self.parent = parent
        self.db_manager = db_manager
        self.ai_integration = ai_integration
        self.theme = ModernTheme()
        
        # Tabs
        self.tabs = [
            {"key": "db", "icon": "🗄️", "label": "DB"},
            {"key": "trigger", "icon": "🔔", "label": "TRIGGER"},
            {"key": "view", "icon": "📊", "label": "VIEW"},
            {"key": "function", "icon": "ƒ", "label": "FUNCTION"},
            {"key": "index", "icon": "🔍", "label": "INDEX"},
            {"key": "procedure", "icon": "⚙️", "label": "PROCEDURE"},
        ]
        self.active_tab_key = None
        self.panel_frames = {}

        self.create_sidebar()
        
    def create_sidebar(self):
        """Create the horizontal-tab sidebar with full-area panels."""
        # Main sidebar frame
        self.sidebar_frame = ttk.Frame(self.parent, style="SideNav.TFrame")
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        # Top horizontal emoji tab bar
        self.create_tab_bar()

        # Content container
        self.content_container = ttk.Frame(self.sidebar_frame, style="SideNav.TFrame")
        self.content_container.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Default empty state
        self.empty_state = ttk.Frame(self.content_container, style="SideNav.TFrame")
        self.empty_state.pack(fill=tk.BOTH, expand=True)
        empty_label = ttk.Label(self.empty_state, text="Select a tab", font=("Segoe UI", 11, "bold"), foreground="#1a1a1a")
        empty_label.pack(expand=True)
    
    def create_tab_bar(self):
        tabbar = ttk.Frame(self.sidebar_frame, style="SideNav.TFrame")
        tabbar.pack(fill=tk.X, padx=8, pady=8)

        self._tab_buttons = {}

        for tab in self.tabs:
            btn = tk.Label(
                tabbar,
                text=tab["icon"],
                fg="#333333",
                bg="#ffffff",
                bd=0,
                font=("Segoe UI Emoji", 16, "normal"),
                relief="flat",
                cursor="hand2",
                highlightthickness=0,
                padx=0,
                pady=0
            )
            btn.pack(side=tk.LEFT, padx=8)
            btn.bind("<Button-1>", lambda e, key=tab["key"]: self.switch_tab(key))
            btn.bind("<Enter>", lambda e, b=btn: self._update_tab_hover_enter(b))
            btn.bind("<Leave>", lambda e, b=btn: self._update_tab_hover_leave(b))
            self._tab_buttons[tab["key"]] = btn
    
    def _update_tab_hover_enter(self, btn):
        """Update tab button style when mouse enters."""
        btn.config(fg="#0066CC")

    def _update_tab_hover_leave(self, btn):
        """Update tab button style when mouse leaves."""
        # Get the tab key for this button
        for key, b in self._tab_buttons.items():
            if b == btn:
                if key == self.active_tab_key:
                    btn.config(fg="#FFA500")
                else:
                    btn.config(fg="#333333")
                break

    def _update_active_tab_styles(self):
        for key, btn in self._tab_buttons.items():
            if key == self.active_tab_key:
                btn.config(font=("Segoe UI Emoji", 16, "bold"), fg="#FFA500")
            else:
                btn.config(font=("Segoe UI Emoji", 16, "normal"), fg="#333333")

    def switch_tab(self, tab_key):
        # Allow re-selecting the same tab
        for child in self.content_container.winfo_children():
            child.pack_forget()
        self.active_tab_key = tab_key
        self._update_active_tab_styles()
        if tab_key not in self.panel_frames:
            if tab_key == "db":
                self.panel_frames[tab_key] = self._create_db_panel(self.content_container)
            elif tab_key == "trigger":
                self.panel_frames[tab_key] = self._create_list_panel(self.content_container, "Triggers", "trigger")
            elif tab_key == "view":
                self.panel_frames[tab_key] = self._create_list_panel(self.content_container, "Views", "view")
            elif tab_key == "function":
                self.panel_frames[tab_key] = self._create_list_panel(self.content_container, "Functions", "function")
            elif tab_key == "index":
                self.panel_frames[tab_key] = self._create_list_panel(self.content_container, "Indexes", "index")
            elif tab_key == "procedure":
                self.panel_frames[tab_key] = self._create_list_panel(self.content_container, "Procedures", "procedure")
        panel = self.panel_frames.get(tab_key)
        if panel is not None:
            panel.pack(fill=tk.BOTH, expand=True)
            # Refresh database header and tree if DB tab is active
            if tab_key == "db":
                if hasattr(self, "db_header_label"):
                    self._update_db_header()
                if hasattr(self, "db_tree"):
                    self._populate_db_tree()
            else:
                # Refresh other panels to sync with current database
                self._refresh_panel_data(tab_key)
        else:
            self.empty_state.pack(fill=tk.BOTH, expand=True)
    
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

        # DB Header - shows currently loaded database with unselect option (reduced size)
        db_header_frame = ttk.Frame(panel, style="SideNav.TFrame")
        db_header_frame.pack(fill=tk.X, padx=8, pady=(6, 2))
        
        current_db = self.db_manager.current_db if hasattr(self.db_manager, "current_db") else None
        db_name = current_db if current_db else "No database loaded"
        
        # Header label container
        header_label_frame = ttk.Frame(db_header_frame, style="SideNav.TFrame")
        header_label_frame.pack(fill=tk.X)
        
        self.db_header_label = tk.Label(
            header_label_frame,
            text=f"🗄️ DB → {db_name}",
            font=("Segoe UI", 10, "bold"),
            fg="#333333",
            bg="#ffffff",
            bd=0,
            relief="flat",
            highlightthickness=0
        )
        self.db_header_label.pack(side=tk.LEFT, anchor=tk.W)
        
        # Unselect button (only shown when a database is loaded, smaller size)
        if current_db:
            self.db_unselect_btn = tk.Button(
                header_label_frame,
                text="✕",
                font=("Segoe UI", 8, "bold"),
                bg="#ffffff",
                fg="#666666",
                bd=1,
                relief="flat",
                padx=4,
                pady=1,
                command=self._unselect_database,
                cursor="hand2",
                width=2,
                height=1
            )
            self.db_unselect_btn.pack(side=tk.RIGHT, padx=(4, 0))
            self.db_unselect_btn.bind("<Enter>", lambda e: self.db_unselect_btn.config(bg="#ffebee", fg="#d32f2f"))
            self.db_unselect_btn.bind("<Leave>", lambda e: self.db_unselect_btn.config(bg="#ffffff", fg="#666666"))
        else:
            self.db_unselect_btn = None
        
        search = self._create_search_bar(panel, "Search…")

        # Tree view without preview area
        tree = ttk.Treeview(panel, show="tree", selectmode="browse")
        tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.db_tree = tree
        self.db_search_entry = search

        tree.bind("<Double-1>", self._on_db_tree_double_click)
        tree.bind("<Button-1>", self._on_db_tree_single_click)
        tree.bind("<Button-3>", self._on_db_tree_right_click)
        search.bind("<KeyRelease>", self._on_db_search_change)

        self._populate_db_tree()

        return panel
    
    def _update_db_header(self):
        """Update the DB header with current database name."""
        if hasattr(self, "db_header_label"):
            current_db = self.db_manager.current_db if hasattr(self.db_manager, "current_db") else None
            db_name = current_db if current_db else "No database loaded"
            self.db_header_label.config(text=f"🗄️ DB → {db_name}")
            
            # Show/hide unselect button based on whether a database is loaded
            if hasattr(self, "db_unselect_btn") and self.db_unselect_btn is not None:
                if current_db:
                    # Show unselect button (reduced padding)
                    try:
                        self.db_unselect_btn.pack(side=tk.RIGHT, padx=(4, 0))
                    except:
                        pass
                else:
                    # Hide unselect button
                    try:
                        self.db_unselect_btn.pack_forget()
                    except:
                        pass
    
    def _unselect_database(self):
        """Unselect/disconnect from the current database."""
        try:
            # Close/disconnect the current database
            if hasattr(self.db_manager, "close_database"):
                self.db_manager.close_database()
            elif hasattr(self.db_manager, "current_db"):
                self.db_manager.current_db = None
            
            # Update header
            self._update_db_header()
            
            # Refresh tree to show available databases
            self._populate_db_tree()
            
            # Refresh all other panels to clear them
            for panel_key in ["trigger", "view", "function", "index", "procedure"]:
                self._refresh_panel_data(panel_key)
            
            # Clear SQL editor if available
            if hasattr(self, 'sql_editor') and self.sql_editor and hasattr(self.sql_editor, 'editor'):
                current_text = self.sql_editor.editor.get("1.0", tk.END).strip()
                if current_text.startswith("-- Current Database:"):
                    self.sql_editor.editor.delete("1.0", tk.END)
        except Exception as e:
            print(f"Error unselecting database: {e}")
    
    def refresh_all_panels(self):
        """Refresh all panels after database changes (CREATE/ALTER/DROP operations)."""
        # Refresh DB panel if it exists
        if hasattr(self, "db_tree"):
            self._populate_db_tree()
        
        # Refresh all other panels
        for panel_key in ["trigger", "view", "function", "index", "procedure"]:
            self._refresh_panel_data(panel_key)
    
    def _switch_database(self, db_name):
        """Switch to the selected database and update UI."""
        try:
            if self.db_manager.open_database(db_name):
                # Update header (will show unselect button)
                self._update_db_header()
                
                # Create unselect button if it doesn't exist (smaller size)
                if not hasattr(self, "db_unselect_btn") or self.db_unselect_btn is None:
                    header_frame = self.db_header_label.master
                    self.db_unselect_btn = tk.Button(
                        header_frame,
                        text="✕",
                        font=("Segoe UI", 8, "bold"),
                        bg="#ffffff",
                        fg="#666666",
                        bd=1,
                        relief="flat",
                        padx=4,
                        pady=1,
                        command=self._unselect_database,
                        cursor="hand2",
                        width=2,
                        height=1
                    )
                    self.db_unselect_btn.pack(side=tk.RIGHT, padx=(4, 0))
                    self.db_unselect_btn.bind("<Enter>", lambda e: self.db_unselect_btn.config(bg="#ffebee", fg="#d32f2f"))
                    self.db_unselect_btn.bind("<Leave>", lambda e: self.db_unselect_btn.config(bg="#ffffff", fg="#666666"))
                
                # Refresh the tree view
                self._populate_db_tree()
                
                # Refresh all other panels to sync with the new database
                for panel_key in ["trigger", "view", "function", "index", "procedure"]:
                    self._refresh_panel_data(panel_key)
                
                # Update SQL editor if available
                if hasattr(self, 'sql_editor') and self.sql_editor and hasattr(self.sql_editor, 'editor'):
                    current_text = self.sql_editor.editor.get("1.0", tk.END).strip()
                    if not current_text:
                        self.sql_editor.editor.insert("1.0", f"-- Current Database: {db_name}\n-- Ready to execute SQL queries\n\n")
        except Exception as e:
            print(f"Error switching database {db_name}: {e}")
    
    def _populate_db_tree(self):
        if not hasattr(self, "db_tree"):
            return
        tree = self.db_tree
        for item in tree.get_children():
            tree.delete(item)
            
        current = self.db_manager.current_db if hasattr(self.db_manager, "current_db") else None
        
        if not current:
            # Show available databases to connect (click to open)
            try:
                databases = self.db_manager.get_databases() if hasattr(self.db_manager, "get_databases") else []
            except Exception:
                databases = []
            for db_name in databases:
                tree.insert("", "end", text=f"📜 {db_name}", values=("database", db_name))
            if not databases:
                tree.insert("", "end", text="No databases available")
            return

        # Connected: Show all database objects directly (no duplicate header)

        # Tables section
        tables_node = tree.insert("", "end", text="📋 Tables")
        try:
            tables = self.db_manager.get_tables() if hasattr(self.db_manager, "get_tables") else []
        except Exception:
            tables = []
        for table in tables:
            tree.insert(tables_node, "end", text=table, values=("table", table))
        
        # Views section
        views_node = tree.insert("", "end", text="📊 Views")
        try:
            views = self.db_manager.get_views() if hasattr(self.db_manager, "get_views") else []
        except Exception:
            views = []
        for view in views:
            tree.insert(views_node, "end", text=view, values=("view", view))

        # Functions section
        functions_node = tree.insert("", "end", text="ƒ Functions")
        try:
            functions = self.db_manager.get_functions() if hasattr(self.db_manager, "get_functions") else []
        except Exception:
            functions = []
        for func in functions:
            tree.insert(functions_node, "end", text=func, values=("function", func))
        
        # Triggers section
        triggers_node = tree.insert("", "end", text="🔔 Triggers")
        try:
            triggers = self.db_manager.get_triggers() if hasattr(self.db_manager, "get_triggers") else []
        except Exception:
            triggers = []
        for trigger in triggers:
            tree.insert(triggers_node, "end", text=trigger, values=("trigger", trigger))

        # Indexes section
        indexes_node = tree.insert("", "end", text="🔍 Indexes")
        try:
            indexes = self.db_manager.get_indexes() if hasattr(self.db_manager, "get_indexes") else []
        except Exception:
            indexes = []
        for idx in indexes:
            idx_name = idx.get("name", str(idx)) if isinstance(idx, dict) else str(idx)
            tree.insert(indexes_node, "end", text=idx_name, values=("index", idx_name))
        
        # Procedures section
        procedures_node = tree.insert("", "end", text="⚙️ Procedures")
        try:
            procedures = self.db_manager.get_procedures() if hasattr(self.db_manager, "get_procedures") else []
        except Exception:
            procedures = []
        for proc in procedures:
            tree.insert(procedures_node, "end", text=proc, values=("procedure", proc))
    
    def _on_db_search_change(self, event=None):
        query = (self.db_search_entry.get() or "").strip().lower()
        if not query:
            self._populate_db_tree()
            return
        tree = self.db_tree
        for item in tree.get_children():
            tree.delete(item)
        current = self.db_manager.current_db if hasattr(self.db_manager, "current_db") else None
        
        if not current:
            # Show available databases matching query
            try:
                databases = self.db_manager.get_databases() if hasattr(self.db_manager, "get_databases") else []
            except Exception:
                databases = []
            for db_name in databases:
                if query in db_name.lower():
                    tree.insert("", "end", text=f"📜 {db_name}", values=("database", db_name))
            return

        # Connected: Show all database objects directly (no duplicate header)

        # Tables section
        tables_node = tree.insert("", "end", text="📋 Tables")
        try:
            tables = self.db_manager.get_tables() if hasattr(self.db_manager, "get_tables") else []
        except Exception:
            tables = []
        for table in tables:
            if query in table.lower():
                tree.insert(tables_node, "end", text=table, values=("table", table))

        # Views section
        views_node = tree.insert("", "end", text="📊 Views")
        try:
            views = self.db_manager.get_views() if hasattr(self.db_manager, "get_views") else []
        except Exception:
            views = []
        for view in views:
            if query in view.lower():
                tree.insert(views_node, "end", text=view, values=("view", view))

        # Functions section
        functions_node = tree.insert("", "end", text="ƒ Functions")
        try:
            functions = self.db_manager.get_functions() if hasattr(self.db_manager, "get_functions") else []
        except Exception:
            functions = []
        for func in functions:
            if query in func.lower():
                tree.insert(functions_node, "end", text=func, values=("function", func))

        # Triggers section
        triggers_node = tree.insert("", "end", text="🔔 Triggers")
        try:
            triggers = self.db_manager.get_triggers() if hasattr(self.db_manager, "get_triggers") else []
        except Exception:
            triggers = []
        for trigger in triggers:
            if query in trigger.lower():
                tree.insert(triggers_node, "end", text=trigger, values=("trigger", trigger))

        # Indexes section
        indexes_node = tree.insert("", "end", text="🔍 Indexes")
        try:
            indexes = self.db_manager.get_indexes() if hasattr(self.db_manager, "get_indexes") else []
        except Exception:
            indexes = []
        for idx in indexes:
            idx_name = idx.get("name", str(idx)) if isinstance(idx, dict) else str(idx)
            if query in idx_name.lower():
                tree.insert(indexes_node, "end", text=idx_name, values=("index", idx_name))

        # Procedures section
        procedures_node = tree.insert("", "end", text="⚙️ Procedures")
        try:
            procedures = self.db_manager.get_procedures() if hasattr(self.db_manager, "get_procedures") else []
        except Exception:
            procedures = []
        for proc in procedures:
            if query in proc.lower():
                tree.insert(procedures_node, "end", text=proc, values=("procedure", proc))
    
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

    def _on_db_tree_single_click(self, event):
        """Handle single click - allows opening databases immediately."""
        sel = self.db_tree.selection()
        if not sel:
            return
        node_text = self.db_tree.item(sel[0]).get("text", "")
        values = self.db_tree.item(sel[0]).get("values", [])
        
        # Check if it's a database (when not connected or to switch)
        if values and len(values) > 0 and values[0] == "database":
            db_name = values[1] if len(values) > 1 else node_text.replace("📜 ", "")
            self._switch_database(db_name)
            return
        
        # If not connected but clicked on a database item (with 📜 icon)
        if not (hasattr(self.db_manager, "current_db") and self.db_manager.current_db):
            if node_text.startswith("📜 "):
                db_name = node_text.replace("📜 ", "")
                self._switch_database(db_name)

    def _on_db_tree_double_click(self, event):
        sel = self.db_tree.selection()
        if not sel:
            return
        node_text = self.db_tree.item(sel[0]).get("text", "")
        parent_id = self.db_tree.parent(sel[0])
        
        # Connected: Check parent section
        if parent_id:
            parent_text = self.db_tree.item(parent_id).get("text", "")
            # Tables, Views, Functions, Triggers, Indexes, Procedures: could show details
            # (Placeholder for future implementation)

    def _action_view_data(self):
        messagebox.showinfo("View Data", "Opening data preview…")

    def _action_edit(self):
        messagebox.showinfo("Edit", "Open editor for selected object…")

    def _action_generate_sql(self):
        messagebox.showinfo("Generate SQL", "Generating SQL…")

    def _action_script_create(self):
        messagebox.showinfo("Script CREATE", "Creating CREATE script…")
    
    # Generic list panels
    def _create_list_panel(self, parent, title, panel_type):
        panel = ttk.Frame(parent, style="SideNav.TFrame")
        search_entry = self._create_search_bar(panel, f"Search {title}…")
        listbox = tk.Listbox(panel, bd=0, highlightthickness=0)
        listbox.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        # Store references for refreshing
        panel._listbox = listbox
        panel._panel_type = panel_type
        panel._search_entry = search_entry
        
        # Bind search
        def on_search_change(event=None):
            search_text = search_entry.get()
            placeholder = f"Search {title}…"
            if search_text == placeholder:
                query = ""
            else:
                query = (search_text or "").strip().lower()
            self._populate_list_panel(panel_type, listbox, query)
        search_entry.bind("<KeyRelease>", on_search_change)
        
        # Initial populate
        self._populate_list_panel(panel_type, listbox, "")
        
        return panel
    
    def _populate_list_panel(self, panel_type, listbox, query=""):
        """Populate a list panel with data from the current database."""
        # Clear existing items
        listbox.delete(0, tk.END)
        
        current_db = self.db_manager.current_db if hasattr(self.db_manager, "current_db") else None
        
        if not current_db:
            listbox.insert(tk.END, "No database selected. Open a database first.")
            return
        
        # Get data based on panel type
        try:
            items = []
            if panel_type == "trigger":
                items = self.db_manager.get_triggers() if hasattr(self.db_manager, "get_triggers") else []
            elif panel_type == "view":
                items = self.db_manager.get_views() if hasattr(self.db_manager, "get_views") else []
            elif panel_type == "function":
                items = self.db_manager.get_functions() if hasattr(self.db_manager, "get_functions") else []
            elif panel_type == "index":
                items = self.db_manager.get_indexes() if hasattr(self.db_manager, "get_indexes") else []
            elif panel_type == "procedure":
                items = self.db_manager.get_procedures() if hasattr(self.db_manager, "get_procedures") else []
        except Exception as e:
            items = []
        
        # Filter by query if provided
        if query:
            items = [item for item in items if query in str(item).lower()]
        
        # Populate listbox
        if items:
            for item in items:
                item_name = item.get("name", str(item)) if isinstance(item, dict) else str(item)
                listbox.insert(tk.END, item_name)
        else:
            listbox.insert(tk.END, f"No {panel_type}s found in the current database.")
    
    def _refresh_panel_data(self, panel_key):
        """Refresh the data in a specific panel based on current database."""
        if panel_key not in self.panel_frames:
            return
        
        panel = self.panel_frames[panel_key]
        if hasattr(panel, "_listbox") and hasattr(panel, "_panel_type"):
            query = ""
            if hasattr(panel, "_search_entry"):
                search_text = panel._search_entry.get()
                # Check if it's not the placeholder text
                placeholder = f"Search {panel._panel_type.title()}s…"
                if search_text and search_text.lower() != placeholder.lower():
                    query = search_text.lower().strip()
            self._populate_list_panel(panel._panel_type, panel._listbox, query)
    
    def refresh_functions(self):
        """Refresh the functions list."""
        tree = getattr(self, "functions_tree")
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
        # Add functions if database is selected
        if self.db_manager.current_db:
            try:
                # Get actual functions from database
                functions = self.db_manager.get_functions()
                for func in functions:
                    tree.insert("", "end", text=f"📄 {func}", values=("function", func))
            except:
                # Fallback to sample functions
                tree.insert("", "end", text="📄 calculate_age", values=("function", "calculate_age"))
                tree.insert("", "end", text="📄 format_name", values=("function", "format_name"))
        else:
            tree.insert("", "end", text="📄 Select a database to view functions", values=("placeholder",))
        
        # Bind events
        tree.bind("<Double-1>", self.on_function_double_click)
        tree.bind("<Button-3>", self.on_function_right_click)
    
    def refresh_views(self):
        """Refresh the views list."""
        tree = getattr(self, "views_tree")
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
        # Add views if database is selected
        if self.db_manager.current_db:
            try:
                # Get actual views from database
                views = self.db_manager.get_views()
                for view in views:
                    tree.insert("", "end", text=f"📄 {view}", values=("view", view))
            except:
                # Fallback to sample views
                tree.insert("", "end", text="📄 user_summary", values=("view", "user_summary"))
                tree.insert("", "end", text="📄 product_stats", values=("view", "product_stats"))
        else:
            tree.insert("", "end", text="📄 Select a database to view views", values=("placeholder",))
        
        # Bind events
        tree.bind("<Double-1>", self.on_view_double_click)
        tree.bind("<Button-3>", self.on_view_right_click)
    
    def refresh_triggers(self):
        """Refresh the triggers list."""
        tree = getattr(self, "triggers_tree")
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
        # Add triggers if database is selected
        if self.db_manager.current_db:
            try:
                # Get actual triggers from database
                triggers = self.db_manager.get_triggers()
                for trigger in triggers:
                    tree.insert("", "end", text=f"📄 {trigger}", values=("trigger", trigger))
            except:
                # Fallback to sample triggers
                tree.insert("", "end", text="📄 update_timestamp", values=("trigger", "update_timestamp"))
                tree.insert("", "end", text="📄 audit_log", values=("trigger", "audit_log"))
        else:
            tree.insert("", "end", text="📄 Select a database to view triggers", values=("placeholder",))
        
        # Bind events
        tree.bind("<Double-1>", self.on_trigger_double_click)
        tree.bind("<Button-3>", self.on_trigger_right_click)
    
    def refresh_procedures(self):
        """Refresh the procedures list."""
        tree = getattr(self, "procedures_tree")
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
        # Add procedures if database is selected
        if self.db_manager.current_db:
            try:
                # Get actual procedures from database
                procedures = self.db_manager.get_procedures()
                for proc in procedures:
                    tree.insert("", "end", text=f"📄 {proc}", values=("procedure", proc))
            except:
                # Fallback to sample procedures
                tree.insert("", "end", text="📄 backup_database", values=("procedure", "backup_database"))
                tree.insert("", "end", text="📄 cleanup_old_data", values=("procedure", "cleanup_old_data"))
        else:
            tree.insert("", "end", text="📄 Select a database to view procedures", values=("placeholder",))
        
        # Bind events
        tree.bind("<Double-1>", self.on_procedure_double_click)
        tree.bind("<Button-3>", self.on_procedure_right_click)
    
    
    # Event handlers
    def on_database_single_click(self, event):
        """Handle database single click."""
        try:
            selection = self.databases_tree.selection()
            if selection:
                item = selection[0]
                values = self.databases_tree.item(item)["values"]
                if values and values[0] == "database":
                    db_name = values[1]
                    
                    # Toggle database expand/collapse
                    current_text = self.databases_tree.item(item)["text"]
                    if current_text.startswith("📁"):
                        # Expand database
                        self.databases_tree.item(item, text=current_text.replace("📁", "📂"))
                        # Show children
                        for child in self.databases_tree.get_children(item):
                            self.databases_tree.reattach(child, item, "end")
                    else:
                        # Collapse database
                        self.databases_tree.item(item, text=current_text.replace("📂", "📁"))
                        # Hide children
                        for child in self.databases_tree.get_children(item):
                            self.databases_tree.detach(child)
                    
                    # Open the database
                    print(f"Opening database: {db_name}")
                    try:
                        if self.db_manager and self.db_manager.open_database(db_name):
                            print(f"Successfully opened database: {db_name}")
                            # Refresh all sections
                            self.refresh_functions()
                            self.refresh_views()
                            self.refresh_triggers()
                            self.refresh_procedures()
                            
                            # Update the SQL editor
                            if hasattr(self, 'sql_editor') and self.sql_editor and hasattr(self.sql_editor, 'editor'):
                                # Clear editor and insert database info
                                self.sql_editor.editor.delete("1.0", tk.END)
                                self.sql_editor.editor.insert("1.0", f"-- Current Database: {db_name}\n-- Ready to execute SQL queries\n\n")
                                self.sql_editor.editor.see(tk.END)
                        else:
                            print(f"Failed to open database: {db_name}")
                    except Exception as e:
                        print(f"Error opening database {db_name}: {e}")
        except Exception as e:
            print(f"Error in database single click: {e}")
    
    def on_database_double_click(self, event):
        """Handle database double-click."""
        pass
    
    def on_database_right_click(self, event):
        """Handle database right-click."""
        pass
    
    def on_function_double_click(self, event):
        """Handle function double-click."""
        pass
    
    def on_function_right_click(self, event):
        """Handle function right-click."""
        pass
    
    def on_view_double_click(self, event):
        """Handle view double-click."""
        pass
    
    def on_view_right_click(self, event):
        """Handle view right-click."""
        pass
    
    def on_trigger_double_click(self, event):
        """Handle trigger double-click."""
        pass
    
    def on_trigger_right_click(self, event):
        """Handle trigger right-click."""
        pass
    
    def on_procedure_double_click(self, event):
        """Handle procedure double-click."""
        pass
    
    def on_procedure_right_click(self, event):
        """Handle procedure right-click."""
        pass
    
    # Placeholder methods for actions
    def create_database(self): pass
    def create_function(self): pass
    def create_view(self): pass
    def create_trigger(self): pass
    def create_procedure(self): pass
