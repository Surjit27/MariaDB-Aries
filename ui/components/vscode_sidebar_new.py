import tkinter as tk
import ttkbootstrap as ttk
from ui.components.modern_theme import ModernTheme

class VSCodeSidebar:
    def __init__(self, parent, db_manager, ai_integration):
        self.parent = parent
        self.db_manager = db_manager
        self.ai_integration = ai_integration
        self.theme = ModernTheme()
        
        # Section states
        self.section_states = {
            "databases": True,
            "functions": False,
            "views": False,
            "triggers": False,
            "procedures": False
        }
        
        # Create the sidebar
        self.create_sidebar()
        
    def create_sidebar(self):
        """Create the VS Code-style sidebar."""
        # Main sidebar frame
        self.sidebar_frame = ttk.Frame(self.parent, style="SideNav.TFrame")
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        # Sidebar header
        self.create_header()
        
        # Content area with scrollbar
        self.create_content_area()
        
        # Create sections
        self.create_sections()
        
        # Collapse button at bottom
        self.create_collapse_button()
    
    def create_header(self):
        """Create the sidebar header."""
        header_frame = ttk.Frame(self.sidebar_frame, style="SideNav.TFrame")
        header_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        # EXPLORER title
        title_label = ttk.Label(header_frame, text="EXPLORER", 
                               style="Header.TLabel", font=("Arial", 10, "bold"))
        title_label.pack(side=tk.LEFT, padx=(5, 0), pady=5)
        
        # Collapse button
        collapse_btn = tk.Button(header_frame, text="◀", command=self.toggle_collapse,
                               bg="#1e1e1e", fg="#cccccc", bd=0, font=("Arial", 10),
                               activebackground="#2d2d2d", activeforeground="#ffffff",
                               width=2, height=1)
        collapse_btn.pack(side=tk.RIGHT, padx=(0, 5), pady=5)
    
    def create_content_area(self):
        """Create the scrollable content area."""
        # Content frame
        self.content_frame = ttk.Frame(self.sidebar_frame, style="SideNav.TFrame")
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_sections(self):
        """Create all VS Code-style sections."""
        # Databases section
        self.create_section("databases", "🗄️", "DATABASES", self.create_database, self.refresh_databases)
        
        # Functions section
        self.create_section("functions", "🧩", "FUNCTIONS", self.create_function, self.refresh_functions)
        
        # Views section
        self.create_section("views", "👁️", "VIEWS", self.create_view, self.refresh_views)
        
        # Triggers section
        self.create_section("triggers", "🧨", "TRIGGERS", self.create_trigger, self.refresh_triggers)
        
        # Procedures section
        self.create_section("procedures", "⚙️", "PROCEDURES", self.create_procedure, self.refresh_procedures)
        
        # Initialize with databases populated
        self.refresh_databases()
    
    def create_section(self, section_name, icon, title, create_cmd, refresh_cmd):
        """Create a VS Code-style collapsible section."""
        # Section header
        header_frame = ttk.Frame(self.content_frame, style="SideNav.TFrame")
        header_frame.pack(fill=tk.X, padx=0, pady=(2, 0))
        
        # Toggle button (chevron)
        toggle_btn = tk.Button(header_frame, text="▼" if self.section_states[section_name] else "▶",
                              command=lambda: self.toggle_section(section_name),
                              bg="#1e1e1e", fg="#cccccc", bd=0, 
                              font=("Consolas", 10), width=2, height=1,
                              activebackground="#2d2d2d", activeforeground="#ffffff")
        toggle_btn.pack(side=tk.LEFT, padx=(5, 2), pady=3)
        
        # Section title
        title_btn = tk.Button(header_frame, text=f"{icon} {title}",
                              command=lambda: self.toggle_section(section_name),
                              bg="#1e1e1e", fg="#cccccc", bd=0,
                              font=("Consolas", 10), anchor="w",
                              activebackground="#2d2d2d", activeforeground="#ffffff")
        title_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), pady=3)
        
        # Action buttons
        actions_frame = ttk.Frame(header_frame, style="SideNav.TFrame")
        actions_frame.pack(side=tk.RIGHT, padx=(0, 5))
        
        create_btn = tk.Button(actions_frame, text="+", command=create_cmd,
                              bg="#1e1e1e", fg="#cccccc", bd=0,
                              font=("Consolas", 10), width=2, height=1,
                              activebackground="#007acc", activeforeground="#ffffff")
        create_btn.pack(side=tk.LEFT, padx=1)
        
        refresh_btn = tk.Button(actions_frame, text="↻", command=refresh_cmd,
                               bg="#1e1e1e", fg="#cccccc", bd=0,
                               font=("Consolas", 10), width=2, height=1,
                               activebackground="#007acc", activeforeground="#ffffff")
        refresh_btn.pack(side=tk.LEFT, padx=1)
        
        # Content area
        content_frame = ttk.Frame(self.content_frame, style="SideNav.TFrame")
        if self.section_states[section_name]:
            content_frame.pack(fill=tk.X, padx=(20, 0), pady=0)
        
        # Store references
        setattr(self, f"{section_name}_header", header_frame)
        setattr(self, f"{section_name}_content", content_frame)
        setattr(self, f"{section_name}_toggle", toggle_btn)
        
        # Create treeview for content
        tree = ttk.Treeview(content_frame, show="tree", height=4)
        tree.pack(fill=tk.X, padx=(0, 5), pady=(0, 5))
        
        # Configure treeview styling
        style = ttk.Style()
        style.configure("Treeview", background="#1e1e1e", foreground="#cccccc", 
                       fieldbackground="#1e1e1d", borderwidth=0)
        style.configure("Treeview.Item", padding=(0, 2))
        
        # Store tree reference
        setattr(self, f"{section_name}_tree", tree)
        
        # Add hover effects
        self.add_hover_effects(header_frame, title_btn, create_btn, refresh_btn)
    
    def add_hover_effects(self, header_frame, title_btn, create_btn, refresh_btn):
        """Add hover effects to section elements."""
        def on_enter(event):
            # Only configure bg for tk.Button widgets, not ttk.Frame
            if isinstance(title_btn, tk.Button):
                title_btn.configure(bg="#2d2d2d")
            if isinstance(create_btn, tk.Button):
                create_btn.configure(bg="#2d2d2d")
            if isinstance(refresh_btn, tk.Button):
                refresh_btn.configure(bg="#2d2d2d")
        
        def on_leave(event):
            # Only configure bg for tk.Button widgets, not ttk.Frame
            if isinstance(title_btn, tk.Button):
                title_btn.configure(bg="#1e1e1e")
            if isinstance(create_btn, tk.Button):
                create_btn.configure(bg="#1e1e1e")
            if isinstance(refresh_btn, tk.Button):
                refresh_btn.configure(bg="#1e1e1e")
        
        # Only bind events to button widgets, not frame widgets
        if isinstance(title_btn, tk.Button):
            title_btn.bind("<Enter>", on_enter)
            title_btn.bind("<Leave>", on_leave)
        if isinstance(create_btn, tk.Button):
            create_btn.bind("<Enter>", on_enter)
            create_btn.bind("<Leave>", on_leave)
        if isinstance(refresh_btn, tk.Button):
            refresh_btn.bind("<Enter>", on_enter)
            refresh_btn.bind("<Leave>", on_leave)
    
    def toggle_section(self, section_name):
        """Toggle section visibility."""
        self.section_states[section_name] = not self.section_states[section_name]
        content_frame = getattr(self, f"{section_name}_content")
        toggle_btn = getattr(self, f"{section_name}_toggle")
        
        if self.section_states[section_name]:
            content_frame.pack(fill=tk.X, padx=(20, 0), pady=0)
            toggle_btn.configure(text="▼")
            # Refresh content when expanding
            if section_name == "databases":
                self.refresh_databases()
            elif section_name == "functions":
                self.refresh_functions()
            elif section_name == "views":
                self.refresh_views()
            elif section_name == "triggers":
                self.refresh_triggers()
            elif section_name == "procedures":
                self.refresh_procedures()
        else:
            content_frame.pack_forget()
            toggle_btn.configure(text="▶")
    
    def refresh_databases(self):
        """Refresh the databases list."""
        tree = getattr(self, "databases_tree")
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
        # Get databases and create VS Code-style structure
        databases = self.db_manager.get_databases()
        for db in databases:
            # Create database folder
            db_item = tree.insert("", "end", text=f"📁 {db}", values=("database", db))
            # Add tables as children
            try:
                tables = self.db_manager.get_tables()
                for table in tables:
                    tree.insert(db_item, "end", text=f"📄 {table}", values=("table", table))
            except:
                pass
        
        # Bind events
        tree.bind("<Double-1>", self.on_database_double_click)
        tree.bind("<Button-3>", self.on_database_right_click)
        tree.bind("<Button-1>", self.on_database_single_click)
    
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
    
    def create_collapse_button(self):
        """Create the collapse button at the bottom."""
        collapse_frame = ttk.Frame(self.sidebar_frame, style="SideNav.TFrame")
        collapse_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        collapse_btn = tk.Button(collapse_frame, text="◀", command=self.toggle_collapse,
                               bg="#1e1e1e", fg="#cccccc", bd=0, font=("Arial", 10),
                               activebackground="#2d2d2d", activeforeground="#ffffff",
                               width=2, height=1)
        collapse_btn.pack(side=tk.RIGHT, padx=(0, 5), pady=5)
    
    def toggle_collapse(self):
        """Toggle sidebar collapse."""
        # This would hide/show the sidebar
        pass
    
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
