import tkinter as tk
import ttkbootstrap as ttk
from ui.components.modern_theme import ModernTheme
import os

class VSCodeSidebar:
    def __init__(self, parent, db_manager, ai_integration):
        self.parent = parent
        self.db_manager = db_manager
        self.ai_integration = ai_integration
        self.theme = ModernTheme()
        self.icons = self.theme.get_emoji_icons()
        self.is_collapsed = False
        self.section_states = {
            'databases': True,
            'functions': True,
            'views': True,
            'triggers': True,
            'procedures': True
        }
        self.create_widgets()
        
    def create_widgets(self):
        """Create the VS Code-style sidebar."""
        # Main sidebar frame
        self.sidebar_frame = ttk.Frame(self.parent, style="SideNav.TFrame", width=280)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
        self.sidebar_frame.pack_propagate(False)
        
        # Sidebar header
        self.create_header()
        
        # Main content area with scrollbar
        self.create_content_area()
        
        # Collapse/expand button
        self.create_collapse_button()
        
    def create_header(self):
        """Create the sidebar header."""
        header_frame = ttk.Frame(self.sidebar_frame, style="SideNav.TFrame")
        header_frame.pack(fill=tk.X, padx=8, pady=8)
        
        # Title with VS Code styling
        title_label = ttk.Label(header_frame, text="EXPLORER", 
                               style="Title.TLabel", font=("Consolas", 11, "bold"))
        title_label.pack(anchor=tk.W)
        
        # Separator
        ttk.Separator(header_frame, orient=tk.HORIZONTAL, style="Modern.TSeparator").pack(fill=tk.X, pady=4)
    
    def create_content_area(self):
        """Create the main content area with scrollbar."""
        # Create a simple frame without canvas for better performance
        self.content_frame = ttk.Frame(self.sidebar_frame, style="SideNav.TFrame")
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create VS Code-style sections
        self.create_vscode_sections()
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling."""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def create_vscode_sections(self):
        """Create VS Code-style collapsible sections."""
        # Databases section
        self.create_vscode_section("databases", "🗄️", "DATABASES", self.create_database, self.refresh_databases)
        
        # Functions section
        self.create_vscode_section("functions", "🧩", "FUNCTIONS", self.create_function, self.refresh_functions)
        
        # Views section
        self.create_vscode_section("views", "👁️", "VIEWS", self.create_view, self.refresh_views)
        
        # Triggers section
        self.create_vscode_section("triggers", "🧨", "TRIGGERS", self.create_trigger, self.refresh_triggers)
        
        # Procedures section
        self.create_vscode_section("procedures", "⚙️", "PROCEDURES", self.create_procedure, self.refresh_procedures)
        
        # Initialize with databases expanded and populated
        self.refresh_databases()
    
    def create_vscode_section(self, section_name, icon, title, create_cmd, refresh_cmd):
        """Create a VS Code-style collapsible section."""
        # Section header with VS Code-style look
        header_frame = ttk.Frame(self.content_frame, style="SideNav.TFrame")
        header_frame.pack(fill=tk.X, padx=0, pady=2)
        
        # Toggle button (chevron) - VS Code style
        toggle_btn = tk.Button(header_frame, text="▼" if self.section_states[section_name] else "▶",
                              command=lambda: self.toggle_section(section_name),
                              bg="#1e1e1e", fg="#cccccc", bd=0, 
                              font=("Consolas", 10), width=2, height=1,
                              activebackground="#2d2d2d", activeforeground="#ffffff")
        toggle_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Section title (clickable) - VS Code style
        title_btn = tk.Button(header_frame, text=f"{icon} {title}",
                              command=lambda: self.toggle_section(section_name),
                              bg="#1e1e1e", fg="#cccccc", bd=0,
                              font=("Consolas", 10), anchor="w",
                              activebackground="#2d2d2d", activeforeground="#ffffff")
        title_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=2)
        
        # Action buttons (VS Code style)
        actions_frame = ttk.Frame(header_frame, style="SideNav.TFrame")
        actions_frame.pack(side=tk.RIGHT, padx=2)
        
        create_btn = tk.Button(actions_frame, text="+", command=create_cmd,
                              bg="#1e1e1e", fg="#cccccc", bd=0,
                              font=("Consolas", 10), width=2, height=1,
                              activebackground="#2d2d2d", activeforeground="#ffffff")
        create_btn.pack(side=tk.LEFT, padx=1)
        
        refresh_btn = tk.Button(actions_frame, text="↻", command=refresh_cmd,
                               bg="#1e1e1e", fg="#cccccc", bd=0,
                               font=("Consolas", 10), width=2, height=1,
                               activebackground="#2d2d2d", activeforeground="#ffffff")
        refresh_btn.pack(side=tk.LEFT, padx=1)
        
        # Content area (initially hidden)
        content_frame = ttk.Frame(self.content_frame, style="SideNav.TFrame")
        if self.section_states[section_name]:
            content_frame.pack(fill=tk.X, padx=20, pady=0)
        
        # Store references
        setattr(self, f"{section_name}_header", header_frame)
        setattr(self, f"{section_name}_content", content_frame)
        setattr(self, f"{section_name}_toggle", toggle_btn)
        
        # Create treeview for content with VS Code styling
        tree = ttk.Treeview(content_frame, show="tree", height=3)
        tree.pack(fill=tk.X, padx=5, pady=5)
        
        # Configure treeview to look like VS Code
        style = ttk.Style()
        style.configure("Treeview", background="#1e1e1e", foreground="#cccccc", 
                       fieldbackground="#1e1e1e", borderwidth=0)
        style.configure("Treeview.Item", padding=(2, 2))
        style.map("Treeview", background=[("selected", "#2d2d2d")])
        
        setattr(self, f"{section_name}_tree", tree)
        
        # Initially hide content if section is collapsed
        if not self.section_states[section_name]:
            content_frame.pack_forget()
    
    def toggle_section(self, section_name):
        """Toggle section expand/collapse state."""
        self.section_states[section_name] = not self.section_states[section_name]
        content_frame = getattr(self, f"{section_name}_content")
        toggle_btn = getattr(self, f"{section_name}_toggle")
        
        if self.section_states[section_name]:
            # Expand section
            content_frame.pack(fill=tk.X, padx=20, pady=0)
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
            # Collapse section
            content_frame.pack_forget()
            toggle_btn.configure(text="▶")
    
    def create_collapse_button(self):
        """Create the collapse/expand button."""
        collapse_frame = ttk.Frame(self.sidebar_frame, style="SideNav.TFrame")
        collapse_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=8)
        
        self.collapse_button = tk.Button(collapse_frame, text="◀", 
                                        command=self.toggle_collapse,
                                        bg="#1e1e1e", fg="#cccccc", bd=0,
                                        font=("Consolas", 10), width=3, height=1,
                                        activebackground="#2d2d2d", activeforeground="#ffffff")
        self.collapse_button.pack(fill=tk.X)
        
    def toggle_collapse(self):
        """Toggle the sidebar collapse state."""
        if self.is_collapsed:
            self.sidebar_frame.configure(width=280)
            self.collapse_button.configure(text="◀")
            self.is_collapsed = False
        else:
            self.sidebar_frame.configure(width=50)
            self.collapse_button.configure(text="▶")
            self.is_collapsed = True
    
    # Database methods
    def refresh_databases(self):
        """Refresh the databases list."""
        tree = getattr(self, "databases_tree")
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
        # Get databases and create VS Code-style structure
        databases = self.db_manager.get_databases()
        for db in databases:
            # Create database folder with chevron
            db_item = tree.insert("", "end", text=f"📁 {db}", values=("database", db))
            # Add database files
            tree.insert(db_item, "end", text="📄 schema.sql", values=("file", "schema"))
            tree.insert(db_item, "end", text="📄 data.sql", values=("file", "data"))
            tree.insert(db_item, "end", text="📄 indexes.sql", values=("file", "indexes"))
        
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
            
        # Add sample functions (like VS Code shows files)
        if self.db_manager.current_db:
            tree.insert("", "end", text="📄 calculate_age.sql", values=("file",))
            tree.insert("", "end", text="📄 format_name.sql", values=("file",))
            tree.insert("", "end", text="📄 get_user_stats.sql", values=("file",))
        else:
            tree.insert("", "end", text="📄 No database selected", values=("placeholder",))
        
        # Bind events
        tree.bind("<Double-1>", self.on_function_double_click)
        tree.bind("<Button-3>", self.on_function_right_click)
        
    def refresh_views(self):
        """Refresh the views list."""
        tree = getattr(self, "views_tree")
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
        # Add sample views (like VS Code shows files)
        if self.db_manager.current_db:
            tree.insert("", "end", text="📄 user_summary.sql", values=("file",))
            tree.insert("", "end", text="📄 sales_report.sql", values=("file",))
            tree.insert("", "end", text="📄 active_users.sql", values=("file",))
        else:
            tree.insert("", "end", text="📄 No database selected", values=("placeholder",))
        
        # Bind events
        tree.bind("<Double-1>", self.on_view_double_click)
        tree.bind("<Button-3>", self.on_view_right_click)
        
    def refresh_triggers(self):
        """Refresh the triggers list."""
        tree = getattr(self, "triggers_tree")
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
        # Add sample triggers (like VS Code shows files)
        if self.db_manager.current_db:
            tree.insert("", "end", text="📄 audit_log_trigger.sql", values=("file",))
            tree.insert("", "end", text="📄 update_timestamp.sql", values=("file",))
            tree.insert("", "end", text="📄 validate_email.sql", values=("file",))
        else:
            tree.insert("", "end", text="📄 No database selected", values=("placeholder",))
        
        # Bind events
        tree.bind("<Double-1>", self.on_trigger_double_click)
        tree.bind("<Button-3>", self.on_trigger_right_click)
        
    def refresh_procedures(self):
        """Refresh the procedures list."""
        tree = getattr(self, "procedures_tree")
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
        # Add sample procedures (like VS Code shows files)
        if self.db_manager.current_db:
            tree.insert("", "end", text="📄 backup_database.sql", values=("file",))
            tree.insert("", "end", text="📄 cleanup_old_data.sql", values=("file",))
            tree.insert("", "end", text="📄 generate_report.sql", values=("file",))
        else:
            tree.insert("", "end", text="📄 No database selected", values=("placeholder",))
        
        # Bind events
        tree.bind("<Double-1>", self.on_procedure_double_click)
        tree.bind("<Button-3>", self.on_procedure_right_click)
    
    # Event handlers
    def on_database_single_click(self, event):
        """Handle database single click - toggle expand/collapse and open database."""
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
                    
                    # Also open the database on single click
                    print(f"Single click - attempting to open database: {db_name}")
                    try:
                        if self.db_manager and self.db_manager.open_database(db_name):
                            print(f"Successfully opened database: {db_name}")
                            
                            # Hide other modals to use full area
                            self.hide_other_modals()
                            
                            # Refresh all sections
                            self.refresh_functions()
                            self.refresh_views()
                            self.refresh_triggers()
                            self.refresh_procedures()
                            
                            # Update the SQL editor to show current database
                            if hasattr(self, 'sql_editor') and self.sql_editor and hasattr(self.sql_editor, 'editor'):
                                # Clear editor and insert database info at the top
                                self.sql_editor.editor.delete("1.0", tk.END)
                                self.sql_editor.editor.insert("1.0", f"-- Current Database: {db_name}\n-- Ready to execute SQL queries\n\n")
                                
                                # Move cursor to the end
                                self.sql_editor.editor.see(tk.END)
                        else:
                            print(f"Failed to open database: {db_name}")
                    except Exception as e:
                        print(f"Error opening database {db_name}: {e}")
        except Exception as e:
            print(f"Error in database single click: {e}")
    
    def on_database_double_click(self, event):
        """Handle database double-click."""
        selection = self.databases_tree.selection()
        if selection:
            item = selection[0]
            values = self.databases_tree.item(item)["values"]
            if values and values[0] == "database":
                db_name = values[1]
                print(f"Attempting to open database: {db_name}")
                # Open database
                if self.db_manager.open_database(db_name):
                    print(f"Successfully opened database: {db_name}")
                    # Refresh all sections
                    self.refresh_functions()
                    self.refresh_views()
                    self.refresh_triggers()
                    self.refresh_procedures()
                    
                    # Update the SQL editor to show current database
                    if hasattr(self, 'sql_editor') and self.sql_editor:
                        # Insert a comment showing current database
                        current_text = self.sql_editor.editor.get("1.0", tk.END).strip()
                        if not current_text:
                            self.sql_editor.editor.insert("1.0", f"-- Current Database: {db_name}\n-- Ready to execute SQL queries\n\n")
                else:
                    print(f"Failed to open database: {db_name}")
            
    def on_database_right_click(self, event):
        """Handle database right-click."""
        # Create context menu
        context_menu = tk.Menu(self.parent, tearoff=0)
        context_menu.add_command(label="🗄️ Open Database", command=self.open_database)
        context_menu.add_command(label="✏️ Rename Database", command=self.rename_database)
        context_menu.add_command(label="🗑️ Delete Database", command=self.delete_database)
        context_menu.add_separator()
        context_menu.add_command(label="💾 Backup Database", command=self.backup_database)
        context_menu.add_command(label="📂 Restore Database", command=self.restore_database)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    # Placeholder methods for other event handlers
    def on_function_double_click(self, event): pass
    def on_function_right_click(self, event): pass
    def on_view_double_click(self, event): pass
    def on_view_right_click(self, event): pass
    def on_trigger_double_click(self, event): pass
    def on_trigger_right_click(self, event): pass
    def on_procedure_double_click(self, event): pass
    def on_procedure_right_click(self, event): pass
    
    # Action methods
    def create_database(self):
        """Create a new database."""
        from tkinter import simpledialog, messagebox
        db_name = simpledialog.askstring("Create Database", "Enter database name:")
        if db_name:
            if self.db_manager.create_database(db_name):
                messagebox.showinfo("Success", f"Database '{db_name}' created successfully.")
                self.refresh_databases()
            else:
                messagebox.showerror("Error", f"Failed to create database '{db_name}'.")
    
    def create_function(self):
        """Create a new function."""
        from tkinter import messagebox
        messagebox.showinfo("Create Function", "Function creation dialog will be implemented.")
    
    def create_view(self):
        """Create a new view."""
        from tkinter import messagebox
        messagebox.showinfo("Create View", "View creation dialog will be implemented.")
    
    def create_trigger(self):
        """Create a new trigger."""
        from tkinter import messagebox
        messagebox.showinfo("Create Trigger", "Trigger creation dialog will be implemented.")
    
    def create_procedure(self):
        """Create a new procedure."""
        from tkinter import messagebox
        messagebox.showinfo("Create Procedure", "Procedure creation dialog will be implemented.")
    
    def hide_other_modals(self):
        """Hide other modals to use full area when opening database."""
        try:
            # Hide any existing popups or modals
            if hasattr(self, 'sql_editor') and self.sql_editor:
                # Close any existing AI popups
                for widget in self.sql_editor.winfo_children():
                    if isinstance(widget, tk.Toplevel):
                        widget.destroy()
        except Exception as e:
            print(f"Error hiding modals: {e}")
    
    # Placeholder methods for other actions
    def open_database(self): pass
    def rename_database(self): pass
    def delete_database(self): pass
    def backup_database(self): pass
    def restore_database(self): pass
