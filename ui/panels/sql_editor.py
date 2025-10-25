import tkinter as tk
import ttkbootstrap as ttk
from db.database_manager import DatabaseManager
from ai.gemini_integration import GeminiIntegration
from ui.components.simple_ai_prompt import SimpleAIPrompt

class SQLEditorPanel(ttk.Frame):
    def __init__(self, parent, db_manager: DatabaseManager, ai_integration: GeminiIntegration = None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.ai_integration = ai_integration
        self.results_viewer = None  # To be set by main app for communication
        self.sidebar = None  # To be set by main app for communication
        self.simple_ai_prompt = None
        self.create_widgets()

    def create_widgets(self):
        label = ttk.Label(self, text="SQL Editor")
        label.pack(pady=5)
        
        # Text area for SQL query input
        self.editor = tk.Text(self, height=10, wrap=tk.WORD, undo=True)
        self.editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add helpful placeholder text
        self.editor.insert("1.0", "-- Welcome to the SQL Editor!\n-- First, create a database:\n-- CREATE DATABASE mydb;\n-- Then open it and create tables:\n-- CREATE TABLE employees (...);")
        
        # Initialize simple AI prompt
        self.simple_ai_prompt = SimpleAIPrompt(self, self.db_manager, self.ai_integration)
        
        # Buttons for actions
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Run Query", command=self.run_query).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear", command=self.clear_editor).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Generate SQL (AI)", command=self.generate_sql).pack(side=tk.LEFT, padx=5)
        
        # Additional buttons for database operations
        btn_frame2 = ttk.Frame(self)
        btn_frame2.pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(btn_frame2, text="Create Database", command=self.create_database_quick).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="Open Database", command=self.open_database_quick).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="🤖 AI Generate", command=self.show_ai_generate).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="⚡ AI Optimize", command=self.show_ai_optimize).pack(side=tk.LEFT, padx=5)

    def set_results_viewer(self, results_viewer):
        """Set the ResultsViewerPanel instance for communication."""
        self.results_viewer = results_viewer

    def set_sidebar(self, sidebar):
        """Set the SidebarPanel instance for communication."""
        self.sidebar = sidebar

    def run_query(self):
        # Get the SQL query from the editor
        query = self.editor.get("1.0", tk.END).strip()
        if not query:
            if self.results_viewer:
                self.results_viewer.display_error("No query to run.")
            return
        
        # Execute the query using DatabaseManager
        column_names, results, error_msg = self.db_manager.execute_query(query)
        
        # Check if this was a database operation that requires sidebar refresh
        query_upper = query.strip().upper()
        if (query_upper.startswith("CREATE DATABASE") or 
            query_upper.startswith("USE") or
            query_upper.startswith("DROP DATABASE") or
            query_upper.startswith("CREATE TABLE") or
            query_upper.startswith("DROP TABLE")):
            if self.sidebar:
                self.sidebar.refresh_databases()
        
        if self.results_viewer:
            if error_msg:
                self.results_viewer.display_error(error_msg)
            elif query_upper.startswith("SELECT"):
                if results:
                    self.results_viewer.display_results(column_names, results)
                else:
                    self.results_viewer.display_error("No results returned.")
            else:
                # Show success message with current database info
                current_db = self.db_manager.current_db
                if current_db:
                    self.results_viewer.display_error(f"Query executed successfully. Current database: {current_db}")
                else:
                    self.results_viewer.display_error("Query executed successfully.")
        else:
            print("Results viewer not set.")

    def clear_editor(self):
        # Clear the text area
        self.editor.delete("1.0", tk.END)

    def generate_sql(self):
        # Check if AI integration is available
        if not self.ai_integration:
            if self.results_viewer:
                self.results_viewer.display_error("AI integration not available. API key may not be set.")
            return
        
        # Get current text or schema info for prompt (placeholder for schema extraction)
        current_text = self.editor.get("1.0", tk.END).strip()
        if current_text:
            prompt = f"Generate an SQL query based on: {current_text}"
        else:
            prompt = "Generate a sample SQL query for a typical database."
        
        # Generate SQL using Gemini API
        generated_query = self.ai_integration.generate_sql_query(prompt)
        if generated_query:
            # Insert the generated query into the editor
            self.clear_editor()
            self.editor.insert("1.0", generated_query)
            if self.results_viewer:
                self.results_viewer.display_error("AI-generated SQL inserted. Review and click 'Run Query' to execute.")
        else:
            if self.results_viewer:
                self.results_viewer.display_error("Failed to generate SQL query with AI.")

    def create_database_quick(self):
        """Quick database creation with user prompt."""
        from tkinter import simpledialog, messagebox
        db_name = simpledialog.askstring("Create Database", "Enter database name:", parent=self)
        if db_name:
            print(f"Attempting to create database: {db_name}")
            print(f"Database manager path: {self.db_manager.db_path}")
            if self.db_manager.create_database(db_name):
                messagebox.showinfo("Success", f"Database '{db_name}' created successfully.", parent=self)
                if self.sidebar:
                    self.sidebar.refresh_databases()
            else:
                messagebox.showerror("Error", f"Failed to create database '{db_name}'. Check console for details.", parent=self)

    def open_database_quick(self):
        """Quick database opening with user prompt."""
        from tkinter import simpledialog, messagebox
        db_name = simpledialog.askstring("Open Database", "Enter database name:", parent=self)
        if db_name:
            if self.db_manager.open_database(db_name):
                messagebox.showinfo("Success", f"Database '{db_name}' opened successfully.", parent=self)
                if self.sidebar:
                    self.sidebar.refresh_databases()
            else:
                messagebox.showerror("Error", f"Failed to open database '{db_name}'.")
    
    def show_ai_generate(self):
        """Show the AI generate prompt."""
        if self.simple_ai_prompt:
            self.simple_ai_prompt.show_prompt()
    
    def show_ai_optimize(self):
        """Show the AI optimize prompt with selected text."""
        if self.simple_ai_prompt:
            # Get selected text
            try:
                selected_text = self.editor.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.simple_ai_prompt.show_prompt(selected_text=selected_text)
            except tk.TclError:
                self.simple_ai_prompt.show_prompt()
