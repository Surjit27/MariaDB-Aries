import tkinter as tk
import ttkbootstrap as ttk
import os
from db.enhanced_database_manager import EnhancedDatabaseManager
from ai.gemini_integration import GeminiIntegration
from utils.session_manager import SessionManager
from ui.panels.sidebar import SidebarPanel
from ui.panels.sql_editor import SQLEditorPanel
from ui.panels.results_viewer import ResultsViewerPanel
from ui.components.query_builder import QueryBuilder
from ui.components.query_history import QueryHistoryPanel
from ui.components.schema_visualizer import SchemaVisualizer
from ui.components.improved_tooltip import create_improved_tooltip
from ui.components.modern_theme import ModernTheme
from ui.components.vscode_sidebar_new import VSCodeSidebar
from ui.components.enhanced_sql_editor import EnhancedSQLEditor
from ui.components.modern_modals import ModernModals
from ui.components.settings_panel import SettingsPanel
from utils.data_export_import import DataExportImport
from utils.settings_manager import SettingsManager

class DBMSWorkbench(ttk.Window):
    def __init__(self):
        # Initialize Settings Manager first
        self.settings_manager = SettingsManager()
        
        # Force light theme (white mode)
        initial_theme = "flatly"  # Always use light theme
        super().__init__(themename=initial_theme)
        self.title("MariaDB:Aries Version - SQL Compiler")
        
        # Initialize modern theme
        self.theme = ModernTheme()
        self.enhanced_modals = None
        self.geometry("1200x800")
        self.minsize(768, 600)  # Minimum size for responsive design
        
        # Set API key from settings or fallback
        api_key = self.settings_manager.get_api_key_value()
        if api_key:
            os.environ['GEMINI_API_KEY'] = api_key
        else:
            # Fallback to hardcoded key if no settings
            os.environ['GEMINI_API_KEY'] = 'AIzaSyCcY01MZsIFwm1li0IAf_pk5knwo6emVjo'
        
        # Initialize Enhanced Database Manager
        db_storage_path = os.path.join(os.getcwd(), "databases")
        print(f"Database storage path: {db_storage_path}")
        print(f"Current working directory: {os.getcwd()}")
        self.db_manager = EnhancedDatabaseManager(db_storage_path)
        
        # Initialize Data Export/Import
        self.data_exporter = DataExportImport(self.db_manager)
        
        # Initialize Gemini API Integration
        self.ai_integration = GeminiIntegration()
        
        # Initialize Modern Modals
        self.modern_modals = ModernModals(self, self.db_manager, self.ai_integration)
        
        # Initialize Session Manager
        session_storage_path = os.path.join(os.getcwd(), "sessions")
        self.session_manager = SessionManager(session_storage_path)
        
        # Theme variable - force light theme
        self.current_theme = "flatly"

        self.create_ui()

    def create_ui(self):
        # Create menu bar
        self.create_menu_bar()
        
        # Create main notebook for all tabs with modern styling
        self.main_notebook = ttk.Notebook(self, style="Modern.TNotebook")
        self.main_notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # SQL Editor Tab (Main working area)
        self.sql_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.sql_tab, text="SQL Editor")
        
        # Create SQL Editor layout
        sql_container = ttk.PanedWindow(self.sql_tab, orient=tk.HORIZONTAL)
        sql_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # VS Code-style Side Navigation (Database Explorer)
        self.side_nav = VSCodeSidebar(sql_container, self.db_manager, self.ai_integration)
        sql_container.add(self.side_nav.sidebar_frame, weight=1)
        
        

        # Central container for SQL Editor and Results Viewer
        central_container = ttk.PanedWindow(sql_container, orient=tk.VERTICAL)
        sql_container.add(central_container, weight=3)

        # Enhanced SQL Editor
        self.sql_editor = EnhancedSQLEditor(central_container, self.db_manager, self.ai_integration)
        central_container.add(self.sql_editor.editor_frame, weight=2)
        
        # Connect side navigation to SQL editor
        self.side_nav.sql_editor = self.sql_editor

        # Results Viewer with adjustable size
        self.results_viewer = ResultsViewerPanel(central_container)
        central_container.add(self.results_viewer, weight=1)
        
        # Connect SQL Editor to Results Viewer and Side Navigation
        self.sql_editor.set_results_viewer(self.results_viewer)
        self.sql_editor.set_sidebar(self.side_nav)

        # Query Builder Tab
        self.query_builder_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.query_builder_tab, text="Query Builder")
        self.query_builder = QueryBuilder(self.query_builder_tab, self.db_manager, self.on_query_generated)
        self.query_builder.pack(fill=tk.BOTH, expand=True)
        
        # Query History Tab
        self.history_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.history_tab, text="📜 History")
        self.query_history = QueryHistoryPanel(self.history_tab, self.db_manager, self.on_query_selected)
        self.query_history.pack(fill=tk.BOTH, expand=True)
        
        # Favorites Tab
        self.favorites_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.favorites_tab, text="⭐ Favorites")
        self.create_favorites_tab()
        
        # Schema Visualizer Tab
        self.schema_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.schema_tab, text="🗂️ Schema")
        self.schema_visualizer = SchemaVisualizer(self.schema_tab, self.db_manager)
        self.schema_visualizer.pack(fill=tk.BOTH, expand=True)
        
        # Settings Tab
        self.settings_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.settings_tab, text="⚙️ Settings")
        self.settings_panel = SettingsPanel(self.settings_tab, self.settings_manager, 
                                           None, self.on_api_key_changed)
        self.settings_panel.pack(fill=tk.BOTH, expand=True)
        
        
        # Status bar
        self.status_bar = ttk.Frame(self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(self.status_bar, text="Ready | Database: None | Tab: SQL Editor")
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        # Bind tab change event
        self.main_notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # Bind keyboard shortcuts
        self.bind("<Control-r>", lambda event: self.sql_editor.run_query())
        self.bind("<Control-c>", lambda event: self.sql_editor.clear_editor())
        self.bind("<Control-g>", lambda event: self.sql_editor.generate_sql())
        self.bind("<Control-Shift-a>", lambda event: self.sql_editor.show_horizontal_ai_modal())
        self.bind("<Control-f>", lambda event: self.search_sql())
        
        # Tab switching shortcuts
        self.bind("<Control-1>", lambda event: self.main_notebook.select(0))  # SQL Editor
        self.bind("<Control-2>", lambda event: self.main_notebook.select(1))  # Query Builder
        self.bind("<Control-3>", lambda event: self.main_notebook.select(2))  # History
        self.bind("<Control-4>", lambda event: self.main_notebook.select(3))  # Favorites
        self.bind("<Control-5>", lambda event: self.main_notebook.select(4))  # Schema
        self.bind("<Control-6>", lambda event: self.main_notebook.select(5))  # Settings
    
    def on_theme_changed(self, theme: str):
        """Handle theme change from settings."""
        self.current_theme = theme
        self.style.theme_use(theme)
        print(f"Theme changed to: {theme}")
    
    def on_api_key_changed(self):
        """Handle API key change from settings."""
        api_key = self.settings_manager.get_api_key_value()
        if api_key:
            os.environ['GEMINI_API_KEY'] = api_key
            # Reinitialize AI integration with new key
            self.ai_integration = GeminiIntegration()
            print("API key updated and AI integration reinitialized")
    
    def create_favorites_tab(self):
        """Create the favorites tab."""
        # Header
        header_frame = ttk.Frame(self.favorites_tab, style="Content.TFrame")
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = ttk.Label(header_frame, text="⭐ Favorite Queries", 
                               style="Title.TLabel", font=("Consolas", 14, "bold"))
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(header_frame, text="Your most used and saved SQL queries", 
                                  style="Subtitle.TLabel", font=("Consolas", 10))
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Content area
        content_frame = ttk.Frame(self.favorites_tab, style="Content.TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Favorites list
        favorites_list = tk.Listbox(content_frame, 
                                   font=("Consolas", 11),
                                   bg="#ffffff", fg="#333333",
                                   selectbackground="#cce5ff", selectforeground="#000000",
                                   relief="solid", bd=1)
        favorites_list.pack(fill=tk.BOTH, expand=True)
        
        # Add some sample favorites
        sample_favorites = [
            "SELECT * FROM users WHERE active = 1;",
            "SELECT COUNT(*) FROM orders WHERE date >= '2024-01-01';",
            "SELECT u.name, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id;",
            "CREATE INDEX idx_user_email ON users(email));",
            "SELECT * FROM products WHERE price BETWEEN 10 AND 100 ORDER BY name;"
        ]
        
        for favorite in sample_favorites:
            favorites_list.insert(tk.END, favorite)
        
        # Bind double-click to load query
        def on_favorite_double_click(event):
            selection = favorites_list.curselection()
            if selection:
                query = favorites_list.get(selection[0])
                self.sql_editor.editor.delete("1.0", tk.END)
                self.sql_editor.editor.insert("1.0", query)
                self.main_notebook.select(0)  # Switch to SQL Editor tab
        
        favorites_list.bind("<Double-1>", on_favorite_double_click)

    def create_menu_bar(self):
        """Create menu bar with File, Info, Help menus."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Database", command=self.show_create_database_modal)
        file_menu.add_command(label="Open Database", command=self.open_database_quick)
        file_menu.add_separator()
        file_menu.add_command(label="Save Session", command=self.save_session)
        file_menu.add_command(label="Load Session", command=self.load_session)
        file_menu.add_separator()
        file_menu.add_command(label="Backup Database", command=self.backup_database)
        file_menu.add_command(label="Restore Database", command=self.restore_database)
        file_menu.add_separator()
        file_menu.add_command(label="Export Data", command=self.export_data)
        file_menu.add_command(label="Import Data", command=self.import_data)
        file_menu.add_separator()
        file_menu.add_command(label="Settings", command=self.show_settings, accelerator="Ctrl+,")
        
        # Database menu
        database_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Database", menu=database_menu)
        database_menu.add_command(label="Create Database", command=self.show_create_database_modal)
        database_menu.add_command(label="Open Database", command=self.open_database_quick)
        database_menu.add_separator()
        database_menu.add_command(label="Create Table", command=self.show_create_table_modal)
        database_menu.add_command(label="Create View", command=self.show_create_view_modal)
        database_menu.add_command(label="Create Trigger", command=self.show_create_trigger_modal)
        database_menu.add_command(label="Create Function", command=self.show_create_function_modal)
        database_menu.add_separator()
        database_menu.add_command(label="Refresh Schema", command=self.refresh_schema)
        database_menu.add_command(label="Show Statistics", command=self.show_statistics)
        
        # SQL menu
        sql_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="SQL", menu=sql_menu)
        sql_menu.add_command(label="Run Query", command=self.run_sql, accelerator="Ctrl+R")
        sql_menu.add_command(label="Clear Editor", command=self.clear_sql, accelerator="Ctrl+C")
        sql_menu.add_separator()
        sql_menu.add_command(label="AI Generate", command=self.generate_sql, accelerator="Ctrl+G")
        sql_menu.add_command(label="AI Chat", command=lambda: self.sql_editor.show_horizontal_ai_modal(), accelerator="Ctrl+Shift+A")
        sql_menu.add_separator()
        sql_menu.add_command(label="Copy SQL", command=self.copy_sql)
        sql_menu.add_command(label="Search in SQL", command=self.search_sql, accelerator="Ctrl+F")
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Query Builder", command=self.show_query_builder)
        tools_menu.add_command(label="Schema Visualizer", command=self.show_schema_visualizer)
        tools_menu.add_separator()
        tools_menu.add_command(label="Query History", command=self.show_query_history)
        tools_menu.add_command(label="Save Query History", command=self.save_query_history)
        tools_menu.add_command(label="Show Query Statistics", command=self.show_query_stats)
        tools_menu.add_separator()
        tools_menu.add_command(label="Clear Query History", command=self.clear_query_history)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Theme", command=self.toggle_theme)
        view_menu.add_separator()
        view_menu.add_command(label="Refresh Data", command=self.refresh_data)
        
        # Info menu
        info_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Info", menu=info_menu)
        info_menu.add_command(label="About", command=self.show_about)
        info_menu.add_command(label="Show Statistics", command=self.show_statistics)
        info_menu.add_command(label="Query Statistics", command=self.show_query_stats)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Help", command=self.show_help)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_help)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
    
    def save_query_history(self):
        """Manually save query history."""
        if hasattr(self.db_manager, 'force_save_history'):
            self.db_manager.force_save_history()
            from tkinter import messagebox
            messagebox.showinfo("Success", "Query history saved successfully!")
        else:
            from tkinter import messagebox
            messagebox.showerror("Error", "Unable to save query history")
    
    def show_query_stats(self):
        """Show query statistics."""
        if hasattr(self.db_manager, 'get_history_count'):
            total_queries = self.db_manager.get_history_count()
            history = self.db_manager.get_query_history()
            
            # Count by status
            success_count = sum(1 for item in history if item.get('status') == 'success')
            error_count = sum(1 for item in history if 'error' in item.get('status', ''))
            
            stats_text = f"""Query Statistics
            
Total Queries: {total_queries}
Successful: {success_count}
Failed: {error_count}
Success Rate: {(success_count/total_queries*100):.1f}% if total_queries > 0 else 0

Recent Queries:
"""
            # Show last 5 queries
            for i, item in enumerate(history[-5:], 1):
                query_preview = item['query'][:50] + "..." if len(item['query']) > 50 else item['query']
                status = item.get('status', 'Unknown')
                stats_text += f"{i}. {query_preview} ({status})\n"
            
            from tkinter import messagebox
            messagebox.showinfo("Query Statistics", stats_text)
        else:
            from tkinter import messagebox
            messagebox.showerror("Error", "Unable to get query statistics")
    
    # Modern modal methods
    def show_create_database_modal(self):
        """Show modern create database modal."""
        if self.modern_modals:
            self.modern_modals.show_create_database_modal()
    
    def show_create_table_modal(self):
        """Show modern create table modal."""
        if self.modern_modals:
            self.modern_modals.show_create_table_modal()
    
    def show_create_function_modal(self):
        """Show modern create function modal."""
        if self.modern_modals:
            self.modern_modals.show_create_function_modal()
    
    def show_create_view_modal(self):
        """Show modern create view modal."""
        if self.modern_modals:
            self.modern_modals.show_create_view_modal()
    
    def show_create_trigger_modal(self):
        """Show modern create trigger modal."""
        if self.modern_modals:
            self.modern_modals.show_create_trigger_modal()

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        if self.current_theme == "flatly":
            self.current_theme = "darkly"
        else:
            self.current_theme = "flatly"
        self.style.theme_use(self.current_theme)
        print(f"Switched to theme: {self.current_theme}")

    def save_session(self):
        """Save the current session with user prompt for name."""
        session_data = {
            "current_db": self.db_manager.current_db,
            "query_history": self.sql_editor.editor.get("1.0", tk.END).strip(),
            "theme": self.current_theme
        }
        self.session_manager.prompt_save_session(self, session_data)

    def load_session(self):
        """Load a saved session with user prompt for selection."""
        session_data = self.session_manager.prompt_load_session(self)
        if session_data:
            # Apply loaded session data
            current_db = session_data.get("current_db")
            if current_db and self.db_manager.open_database(current_db):
                self.sidebar.refresh_databases()
            query_history = session_data.get("query_history", "")
            if query_history:
                self.sql_editor.clear_editor()
                self.sql_editor.editor.insert("1.0", query_history)
            theme = session_data.get("theme", "darkly")
            if theme != self.current_theme:
                self.current_theme = theme
                self.style.theme_use(self.current_theme)
                print(f"Loaded theme: {self.current_theme}")

    def on_query_generated(self, query: str):
        """Handle query generated from query builder."""
        self.sql_editor.editor.delete(1.0, tk.END)
        self.sql_editor.editor.insert(1.0, query)

    def on_query_selected(self, query: str):
        """Handle query selected from history or favorites."""
        self.sql_editor.editor.delete(1.0, tk.END)
        self.sql_editor.editor.insert(1.0, query)
        # Switch to SQL Editor tab
        self.main_notebook.select(0)

    def on_tab_changed(self, event):
        """Handle tab change event."""
        current_tab = self.main_notebook.index("current")
        tab_names = ["SQL Editor", "Query Builder", "History", "Favorites", "Schema", "Settings"]
        current_tab_name = tab_names[current_tab] if current_tab < len(tab_names) else "Unknown"
        
        # Update status bar
        db_name = self.db_manager.current_db if self.db_manager.current_db else "None"
        self.status_label.config(text=f"Ready | Database: {db_name} | Tab: {current_tab_name}")
        
        # Refresh data when switching to certain tabs
        if current_tab == 2:  # History tab
            self.query_history.refresh_data()
        elif current_tab == 4:  # Schema tab
            self.schema_visualizer.refresh_schema()
        elif current_tab == 5:  # Settings tab
            self.settings_panel.refresh_api_keys()

    def update_status(self, message: str):
        """Update status bar message."""
        db_name = self.db_manager.current_db if self.db_manager.current_db else "None"
        current_tab = self.main_notebook.index("current")
        tab_names = ["SQL Editor", "Query Builder", "History & Favorites", "Schema"]
        current_tab_name = tab_names[current_tab] if current_tab < len(tab_names) else "Unknown"
        self.status_label.config(text=f"{message} | Database: {db_name} | Tab: {current_tab_name}")

    def backup_database(self):
        """Backup current database."""
        if not self.db_manager.current_db:
            from tkinter import messagebox
            messagebox.showwarning("Warning", "No database is currently open.")
            return
        
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")],
            initialvalue=f"{self.db_manager.current_db}_backup.db"
        )
        if filename:
            if self.data_exporter.backup_database(self.db_manager.current_db, filename):
                from tkinter import messagebox
                messagebox.showinfo("Success", f"Database backed up to {filename}")

    def restore_database(self):
        """Restore database from backup."""
        from tkinter import filedialog, simpledialog, messagebox
        backup_file = filedialog.askopenfilename(
            filetypes=[("Database files", "*.db"), ("All files", "*.*")]
        )
        if backup_file:
            db_name = simpledialog.askstring("Restore Database", "Enter database name:")
            if db_name:
                if self.data_exporter.restore_database(backup_file, db_name):
                    messagebox.showinfo("Success", f"Database restored as {db_name}")
                    self.sidebar.refresh_databases()

    def export_data(self):
        """Export data from current table."""
        if not self.db_manager.current_db:
            from tkinter import messagebox
            messagebox.showwarning("Warning", "No database is currently open.")
            return
        
        tables = self.db_manager.get_tables()
        if not tables:
            from tkinter import messagebox
            messagebox.showwarning("Warning", "No tables found in current database.")
            return
        
        from tkinter import simpledialog, filedialog, messagebox
        table_name = simpledialog.askstring("Export Data", "Enter table name:")
        if table_name and table_name in tables:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("SQL files", "*.sql"), ("All files", "*.*")]
            )
            if filename:
                if filename.endswith('.csv'):
                    success = self.data_exporter.export_to_csv(table_name, filename)
                elif filename.endswith('.json'):
                    success = self.data_exporter.export_to_json(table_name, filename)
                elif filename.endswith('.sql'):
                    success = self.data_exporter.export_to_sql(table_name, filename)
                else:
                    success = self.data_exporter.export_to_csv(table_name, filename)
                
                if success:
                    messagebox.showinfo("Success", f"Data exported to {filename}")

    def import_data(self):
        """Import data to current database."""
        if not self.db_manager.current_db:
            from tkinter import messagebox
            messagebox.showwarning("Warning", "No database is currently open.")
            return
        
        from tkinter import filedialog, simpledialog, messagebox
        filename = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            table_name = simpledialog.askstring("Import Data", "Enter table name:")
            if table_name:
                if filename.endswith('.csv'):
                    success = self.data_exporter.import_from_csv(table_name, filename)
                elif filename.endswith('.json'):
                    success = self.data_exporter.import_from_json(table_name, filename)
                else:
                    success = self.data_exporter.import_from_csv(table_name, filename)
                
                if success:
                    messagebox.showinfo("Success", f"Data imported to {table_name}")
                    self.sidebar.refresh_databases()

    def refresh_schema(self):
        """Refresh database schema."""
        if self.db_manager.current_db:
            self.db_manager.load_database_schema()
            self.schema_visualizer.refresh_schema()
            from tkinter import messagebox
            messagebox.showinfo("Success", "Schema refreshed successfully")

    def show_query_history(self):
        """Show query history tab."""
        self.main_notebook.select(2)  # History tab

    def show_query_builder(self):
        """Show query builder tab."""
        self.main_notebook.select(1)  # Query Builder tab

    def show_schema_visualizer(self):
        """Show schema visualizer tab."""
        self.main_notebook.select(3)  # Schema tab

    def clear_query_history(self):
        """Clear query history."""
        from tkinter import messagebox
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all query history?"):
            self.db_manager.query_history = []
            self.db_manager.save_query_history()
            self.query_history.refresh_history()
            messagebox.showinfo("Success", "Query history cleared")

    # Header bar button methods
    def create_database_quick(self):
        """Quick database creation."""
        from tkinter import simpledialog, messagebox
        db_name = simpledialog.askstring("Create Database", "Enter database name:")
        if db_name:
            if self.db_manager.create_database(db_name):
                messagebox.showinfo("Success", f"Database '{db_name}' created successfully")
                self.sidebar.refresh_databases()
            else:
                messagebox.showerror("Error", f"Failed to create database '{db_name}'")

    def open_database_quick(self):
        """Quick database opening."""
        from tkinter import simpledialog, messagebox
        db_name = simpledialog.askstring("Open Database", "Enter database name:")
        if db_name:
            if self.db_manager.open_database(db_name):
                messagebox.showinfo("Success", f"Database '{db_name}' opened successfully")
                self.sidebar.refresh_databases()
            else:
                messagebox.showerror("Error", f"Failed to open database '{db_name}'")

    def run_sql(self):
        """Run SQL from editor."""
        self.sql_editor.run_query()

    def clear_sql(self):
        """Clear SQL editor."""
        self.sql_editor.clear_editor()

    def generate_sql(self):
        """Generate SQL using AI."""
        self.sql_editor.generate_sql()

    def copy_sql(self):
        """Copy SQL from editor."""
        sql_text = self.sql_editor.editor.get(1.0, tk.END).strip()
        self.clipboard_clear()
        self.clipboard_append(sql_text)
    

    def search_sql(self):
        """Search in SQL editor."""
        from tkinter import simpledialog
        search_text = simpledialog.askstring("Search", "Enter text to search:")
        if search_text:
            content = self.sql_editor.editor.get(1.0, tk.END)
            if search_text.lower() in content.lower():
                from tkinter import messagebox
                messagebox.showinfo("Search", f"Found '{search_text}' in SQL editor")
            else:
                from tkinter import messagebox
                messagebox.showinfo("Search", f"'{search_text}' not found")

    def copy_results(self):
        """Copy results from viewer."""
        if hasattr(self.results_viewer, 'copy_all'):
            self.results_viewer.copy_all()

    def refresh_data(self):
        """Refresh data in current view."""
        if self.db_manager.current_db:
            self.sidebar.refresh_databases()
            self.update_status("Data refreshed")

    def create_trigger(self):
        """Create a trigger."""
        from tkinter import simpledialog, messagebox
        trigger_name = simpledialog.askstring("Create Trigger", "Enter trigger name:")
        if trigger_name:
            trigger_sql = f"""
CREATE TRIGGER {trigger_name}
AFTER INSERT ON table_name
BEGIN
    -- Trigger logic here
END;
"""
            self.sql_editor.editor.insert(tk.END, trigger_sql)
            messagebox.showinfo("Success", f"Trigger template for '{trigger_name}' added to editor")

    def create_function(self):
        """Create a function."""
        from tkinter import simpledialog, messagebox
        function_name = simpledialog.askstring("Create Function", "Enter function name:")
        if function_name:
            function_sql = f"""
CREATE FUNCTION {function_name}(param1 TEXT)
RETURNS TEXT
BEGIN
    -- Function logic here
    RETURN param1;
END;
"""
            self.sql_editor.editor.insert(tk.END, function_sql)
            messagebox.showinfo("Success", f"Function template for '{function_name}' added to editor")

    def create_view(self):
        """Create a view."""
        from tkinter import simpledialog, messagebox
        view_name = simpledialog.askstring("Create View", "Enter view name:")
        if view_name:
            view_sql = f"""
CREATE VIEW {view_name} AS
SELECT * FROM table_name
WHERE condition;
"""
            self.sql_editor.editor.insert(tk.END, view_sql)
            messagebox.showinfo("Success", f"View template for '{view_name}' added to editor")

    def show_statistics(self):
        """Show database statistics."""
        if not self.db_manager.current_db:
            from tkinter import messagebox
            messagebox.showwarning("Warning", "No database is currently open")
            return
        
        tables = self.db_manager.get_tables()
        stats_text = f"Database Statistics for '{self.db_manager.current_db}':\n"
        stats_text += f"Number of tables: {len(tables)}\n\n"
        
        for table in tables:
            try:
                columns, data = self.db_manager.get_table_data(table, limit=1)
                row_count = len(data) if data else 0
                stats_text += f"Table '{table}': {len(columns)} columns, {row_count} rows\n"
            except:
                stats_text += f"Table '{table}': Unable to get statistics\n"
        
        stats_window = tk.Toplevel(self)
        stats_window.title("Database Statistics")
        stats_window.geometry("500x400")
        
        text_widget = tk.Text(stats_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, stats_text)
        text_widget.config(state=tk.DISABLED)

    def show_settings(self):
        """Show settings tab."""
        self.main_notebook.select(5)  # Settings tab

    def show_help(self):
        """Show help dialog."""
        help_text = """
DBMS Workbench Help

Keyboard Shortcuts:
- Ctrl+R: Run SQL
- Ctrl+C: Clear Editor
- Ctrl+G: Generate SQL with AI
- Ctrl+1-6: Switch tabs (1=SQL Editor, 2=Query Builder, 3=History, 4=Favorites, 5=Schema, 6=Settings)

Features:
- Create and manage databases
- Execute SQL queries
- Query builder
- Schema visualization
- Data export/import
- Query history and favorites
- Settings with API key management and theme toggle

For more help, check the documentation.
"""
        help_window = tk.Toplevel(self)
        help_window.title("Help")
        help_window.geometry("600x500")
        
        text_widget = tk.Text(help_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, help_text)
        text_widget.config(state=tk.DISABLED)

    def show_about(self):
        """Show about dialog."""
        from tkinter import messagebox
        messagebox.showinfo("About", 
            "Offline PostgreSQL-Style DBMS Workbench\n\n"
            "Version: 1.0\n"
            "A powerful database management tool with AI integration\n"
            "Built with Python, Tkinter, and SQLite")

if __name__ == "__main__":
    app = DBMSWorkbench()
    app.mainloop()
