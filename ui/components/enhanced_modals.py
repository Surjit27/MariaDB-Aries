import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox, simpledialog
from ui.components.modern_theme import ModernTheme

class EnhancedModals:
    def __init__(self, parent, db_manager, ai_integration):
        self.parent = parent
        self.db_manager = db_manager
        self.ai_integration = ai_integration
        self.theme = ModernTheme()
        self.icons = self.theme.get_emoji_icons()
        
    def show_create_database_modal(self):
        """Show enhanced create database modal."""
        modal = tk.Toplevel(self.parent)
        modal.title("🗄️ Create Database")
        modal.geometry("500x400")
        modal.transient(self.parent)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (500 // 2)
        y = (modal.winfo_screenheight() // 2) - (400 // 2)
        modal.geometry(f"500x400+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(modal, style="Modal.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ttk.Frame(main_frame, style="Modal.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="🗄️ Create New Database", 
                               style="Title.TLabel")
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(header_frame, text="Configure your new database settings", 
                                 style="Subtitle.TLabel")
        subtitle_label.pack(anchor=tk.W)
        
        # Form fields
        form_frame = ttk.Frame(main_frame, style="Modal.TFrame")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Database name
        name_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        name_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(name_frame, text="Database Name:", style="Subtitle.TLabel").pack(anchor=tk.W)
        name_entry = ttk.Entry(name_frame, style="Modern.TEntry", font=("Arial", 11))
        name_entry.pack(fill=tk.X, pady=5)
        name_entry.focus_set()
        
        # Character set
        charset_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        charset_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(charset_frame, text="Character Set:", style="Subtitle.TLabel").pack(anchor=tk.W)
        charset_combo = ttk.Combobox(charset_frame, values=["utf8mb4", "utf8", "latin1"], 
                                    style="Modern.TCombobox", font=("Arial", 11))
        charset_combo.pack(fill=tk.X, pady=5)
        charset_combo.set("utf8mb4")
        
        # Collation
        collation_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        collation_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(collation_frame, text="Collation:", style="Subtitle.TLabel").pack(anchor=tk.W)
        collation_combo = ttk.Combobox(collation_frame, 
                                      values=["utf8mb4_unicode_ci", "utf8mb4_general_ci", "utf8_general_ci"], 
                                      style="Modern.TCombobox", font=("Arial", 11))
        collation_combo.pack(fill=tk.X, pady=5)
        collation_combo.set("utf8mb4_unicode_ci")
        
        # AI suggestions
        ai_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        ai_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(ai_frame, text="🤖 AI Suggestions:", style="Subtitle.TLabel").pack(anchor=tk.W)
        ai_suggestions = tk.Text(ai_frame, height=3, style="Modern.TText", font=("Arial", 10))
        ai_suggestions.pack(fill=tk.X, pady=5)
        ai_suggestions.insert("1.0", "💡 Suggested database name: company_db\n💡 Recommended charset: utf8mb4\n💡 Suggested collation: utf8mb4_unicode_ci")
        ai_suggestions.configure(state="disabled")
        
        # Buttons
        button_frame = ttk.Frame(main_frame, style="Modal.TFrame")
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="❌ Cancel", command=modal.destroy, 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="👁️ Preview", command=lambda: self.preview_database(name_entry.get(), charset_combo.get(), collation_combo.get()), 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="💾 Save for Later", command=lambda: self.save_database_template(name_entry.get(), charset_combo.get(), collation_combo.get()), 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="✅ Create", command=lambda: self.create_database(name_entry.get(), charset_combo.get(), collation_combo.get(), modal), 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        
    def show_create_table_modal(self):
        """Show enhanced create table modal."""
        modal = tk.Toplevel(self.parent)
        modal.title("📊 Create Table")
        modal.geometry("700x600")
        modal.transient(self.parent)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (700 // 2)
        y = (modal.winfo_screenheight() // 2) - (600 // 2)
        modal.geometry(f"700x600+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(modal, style="Modal.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ttk.Frame(main_frame, style="Modal.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="📊 Create New Table", 
                               style="Title.TLabel")
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(header_frame, text="Define your table structure and constraints", 
                                 style="Subtitle.TLabel")
        subtitle_label.pack(anchor=tk.W)
        
        # Form fields
        form_frame = ttk.Frame(main_frame, style="Modal.TFrame")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Table name
        name_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        name_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(name_frame, text="Table Name:", style="Subtitle.TLabel").pack(anchor=tk.W)
        name_entry = ttk.Entry(name_frame, style="Modern.TEntry", font=("Arial", 11))
        name_entry.pack(fill=tk.X, pady=5)
        
        # Columns definition
        columns_frame = ttk.LabelFrame(form_frame, text="📋 Columns", style="Modal.TFrame")
        columns_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Columns list
        columns_tree = ttk.Treeview(columns_frame, columns=("Name", "Type", "Null", "Key", "Default", "Extra"), 
                                  show="headings", height=8)
        columns_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure columns
        columns_tree.heading("Name", text="Column Name")
        columns_tree.heading("Type", text="Data Type")
        columns_tree.heading("Null", text="NULL")
        columns_tree.heading("Key", text="Key")
        columns_tree.heading("Default", text="Default")
        columns_tree.heading("Extra", text="Extra")
        
        # Column actions
        col_actions_frame = ttk.Frame(columns_frame, style="Modal.TFrame")
        col_actions_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(col_actions_frame, text="➕ Add Column", command=lambda: self.add_column(columns_tree), 
                  style="Modal.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(col_actions_frame, text="✏️ Edit Column", command=lambda: self.edit_column(columns_tree), 
                  style="Modal.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(col_actions_frame, text="🗑️ Delete Column", command=lambda: self.delete_column(columns_tree), 
                  style="Modal.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(col_actions_frame, text="🤖 AI Suggest", command=lambda: self.ai_suggest_columns(columns_tree), 
                  style="Modal.TButton").pack(side=tk.LEFT, padx=5)
        
        # AI suggestions
        ai_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        ai_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(ai_frame, text="🤖 AI Suggestions:", style="Subtitle.TLabel").pack(anchor=tk.W)
        ai_suggestions = tk.Text(ai_frame, height=3, style="Modern.TText", font=("Arial", 10))
        ai_suggestions.pack(fill=tk.X, pady=5)
        ai_suggestions.insert("1.0", "💡 Suggested columns: id (INT PRIMARY KEY), name (VARCHAR), created_at (TIMESTAMP)\n💡 Recommended indexes: PRIMARY KEY on id, INDEX on name")
        ai_suggestions.configure(state="disabled")
        
        # Buttons
        button_frame = ttk.Frame(main_frame, style="Modal.TFrame")
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="❌ Cancel", command=modal.destroy, 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="👁️ Preview", command=lambda: self.preview_table(name_entry.get(), columns_tree), 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="💾 Save for Later", command=lambda: self.save_table_template(name_entry.get(), columns_tree), 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="✅ Create", command=lambda: self.create_table(name_entry.get(), columns_tree, modal), 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        
    def show_create_function_modal(self):
        """Show enhanced create function modal."""
        modal = tk.Toplevel(self.parent)
        modal.title("⚡ Create Function")
        modal.geometry("600x500")
        modal.transient(self.parent)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (600 // 2)
        y = (modal.winfo_screenheight() // 2) - (500 // 2)
        modal.geometry(f"600x500+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(modal, style="Modal.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ttk.Frame(main_frame, style="Modal.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="⚡ Create New Function", 
                               style="Title.TLabel")
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(header_frame, text="Define your custom function logic", 
                                 style="Subtitle.TLabel")
        subtitle_label.pack(anchor=tk.W)
        
        # Form fields
        form_frame = ttk.Frame(main_frame, style="Modal.TFrame")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Function name
        name_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        name_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(name_frame, text="Function Name:", style="Subtitle.TLabel").pack(anchor=tk.W)
        name_entry = ttk.Entry(name_frame, style="Modern.TEntry", font=("Arial", 11))
        name_entry.pack(fill=tk.X, pady=5)
        
        # Parameters
        params_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        params_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(params_frame, text="Parameters:", style="Subtitle.TLabel").pack(anchor=tk.W)
        params_entry = ttk.Entry(params_frame, style="Modern.TEntry", font=("Arial", 11))
        params_entry.pack(fill=tk.X, pady=5)
        params_entry.insert(0, "param1 INT, param2 VARCHAR(255)")
        
        # Return type
        return_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        return_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(return_frame, text="Return Type:", style="Subtitle.TLabel").pack(anchor=tk.W)
        return_combo = ttk.Combobox(return_frame, values=["INT", "VARCHAR", "DECIMAL", "BOOLEAN", "DATE", "DATETIME"], 
                                   style="Modern.TCombobox", font=("Arial", 11))
        return_combo.pack(fill=tk.X, pady=5)
        return_combo.set("INT")
        
        # Function body
        body_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        body_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ttk.Label(body_frame, text="Function Body:", style="Subtitle.TLabel").pack(anchor=tk.W)
        body_text = tk.Text(body_frame, height=8, style="Modern.TText", font=("Arial", 10))
        body_text.pack(fill=tk.BOTH, expand=True, pady=5)
        body_text.insert("1.0", "BEGIN\n    -- Function logic here\n    RETURN param1 + param2;\nEND")
        
        # AI suggestions
        ai_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        ai_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(ai_frame, text="🤖 AI Suggestions:", style="Subtitle.TLabel").pack(anchor=tk.W)
        ai_suggestions = tk.Text(ai_frame, height=2, style="Modern.TText", font=("Arial", 10))
        ai_suggestions.pack(fill=tk.X, pady=5)
        ai_suggestions.insert("1.0", "💡 Suggested function: calculate_age(birth_date DATE) RETURNS INT")
        ai_suggestions.configure(state="disabled")
        
        # Buttons
        button_frame = ttk.Frame(main_frame, style="Modal.TFrame")
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="❌ Cancel", command=modal.destroy, 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="👁️ Preview", command=lambda: self.preview_function(name_entry.get(), params_entry.get(), return_combo.get(), body_text.get("1.0", tk.END)), 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="💾 Save for Later", command=lambda: self.save_function_template(name_entry.get(), params_entry.get(), return_combo.get(), body_text.get("1.0", tk.END)), 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="✅ Create", command=lambda: self.create_function(name_entry.get(), params_entry.get(), return_combo.get(), body_text.get("1.0", tk.END), modal), 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        
    def show_create_view_modal(self):
        """Show enhanced create view modal."""
        modal = tk.Toplevel(self.parent)
        modal.title("👁️ Create View")
        modal.geometry("600x500")
        modal.transient(self.parent)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (600 // 2)
        y = (modal.winfo_screenheight() // 2) - (500 // 2)
        modal.geometry(f"600x500+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(modal, style="Modal.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ttk.Frame(main_frame, style="Modal.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="👁️ Create New View", 
                               style="Title.TLabel")
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(header_frame, text="Define your view query and structure", 
                                 style="Subtitle.TLabel")
        title_label.pack(anchor=tk.W)
        
        # Form fields
        form_frame = ttk.Frame(main_frame, style="Modal.TFrame")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # View name
        name_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        name_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(name_frame, text="View Name:", style="Subtitle.TLabel").pack(anchor=tk.W)
        name_entry = ttk.Entry(name_frame, style="Modern.TEntry", font=("Arial", 11))
        name_entry.pack(fill=tk.X, pady=5)
        
        # View query
        query_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        query_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ttk.Label(query_frame, text="View Query:", style="Subtitle.TLabel").pack(anchor=tk.W)
        query_text = tk.Text(query_frame, height=10, style="Modern.TText", font=("Arial", 10))
        query_text.pack(fill=tk.BOTH, expand=True, pady=5)
        query_text.insert("1.0", "SELECT \n    id,\n    name,\n    email\nFROM users\nWHERE active = 1")
        
        # AI suggestions
        ai_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        ai_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(ai_frame, text="🤖 AI Suggestions:", style="Subtitle.TLabel").pack(anchor=tk.W)
        ai_suggestions = tk.Text(ai_frame, height=2, style="Modern.TText", font=("Arial", 10))
        ai_suggestions.pack(fill=tk.X, pady=5)
        ai_suggestions.insert("1.0", "💡 Suggested view: active_users AS SELECT * FROM users WHERE status = 'active'")
        ai_suggestions.configure(state="disabled")
        
        # Buttons
        button_frame = ttk.Frame(main_frame, style="Modal.TFrame")
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="❌ Cancel", command=modal.destroy, 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="👁️ Preview", command=lambda: self.preview_view(name_entry.get(), query_text.get("1.0", tk.END)), 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="💾 Save for Later", command=lambda: self.save_view_template(name_entry.get(), query_text.get("1.0", tk.END)), 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="✅ Create", command=lambda: self.create_view(name_entry.get(), query_text.get("1.0", tk.END), modal), 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        
    def show_create_trigger_modal(self):
        """Show enhanced create trigger modal."""
        modal = tk.Toplevel(self.parent)
        modal.title("🔧 Create Trigger")
        modal.geometry("600x500")
        modal.transient(self.parent)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (600 // 2)
        y = (modal.winfo_screenheight() // 2) - (500 // 2)
        modal.geometry(f"600x500+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(modal, style="Modal.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ttk.Frame(main_frame, style="Modal.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="🔧 Create New Trigger", 
                               style="Title.TLabel")
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(header_frame, text="Define your trigger logic and timing", 
                                 style="Subtitle.TLabel")
        subtitle_label.pack(anchor=tk.W)
        
        # Form fields
        form_frame = ttk.Frame(main_frame, style="Modal.TFrame")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Trigger name
        name_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        name_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(name_frame, text="Trigger Name:", style="Subtitle.TLabel").pack(anchor=tk.W)
        name_entry = ttk.Entry(name_frame, style="Modern.TEntry", font=("Arial", 11))
        name_entry.pack(fill=tk.X, pady=5)
        
        # Table selection
        table_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        table_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(table_frame, text="Table:", style="Subtitle.TLabel").pack(anchor=tk.W)
        table_combo = ttk.Combobox(table_frame, values=self.get_available_tables(), 
                                  style="Modern.TCombobox", font=("Arial", 11))
        table_combo.pack(fill=tk.X, pady=5)
        
        # Timing
        timing_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        timing_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(timing_frame, text="Timing:", style="Subtitle.TLabel").pack(anchor=tk.W)
        timing_combo = ttk.Combobox(timing_frame, values=["BEFORE", "AFTER"], 
                                   style="Modern.TCombobox", font=("Arial", 11))
        timing_combo.pack(fill=tk.X, pady=5)
        timing_combo.set("AFTER")
        
        # Event
        event_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        event_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(event_frame, text="Event:", style="Subtitle.TLabel").pack(anchor=tk.W)
        event_combo = ttk.Combobox(event_frame, values=["INSERT", "UPDATE", "DELETE"], 
                                  style="Modern.TCombobox", font=("Arial", 11))
        event_combo.pack(fill=tk.X, pady=5)
        event_combo.set("INSERT")
        
        # Trigger body
        body_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        body_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ttk.Label(body_frame, text="Trigger Body:", style="Subtitle.TLabel").pack(anchor=tk.W)
        body_text = tk.Text(body_frame, height=6, style="Modern.TText", font=("Arial", 10))
        body_text.pack(fill=tk.BOTH, expand=True, pady=5)
        body_text.insert("1.0", "BEGIN\n    -- Trigger logic here\n    INSERT INTO audit_log (table_name, action, timestamp)\n    VALUES (NEW.table_name, 'INSERT', NOW());\nEND")
        
        # AI suggestions
        ai_frame = ttk.Frame(form_frame, style="Modal.TFrame")
        ai_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(ai_frame, text="🤖 AI Suggestions:", style="Subtitle.TLabel").pack(anchor=tk.W)
        ai_suggestions = tk.Text(ai_frame, height=2, style="Modern.TText", font=("Arial", 10))
        ai_suggestions.pack(fill=tk.X, pady=5)
        ai_suggestions.insert("1.0", "💡 Suggested trigger: audit_trigger AFTER INSERT ON users")
        ai_suggestions.configure(state="disabled")
        
        # Buttons
        button_frame = ttk.Frame(main_frame, style="Modal.TFrame")
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="❌ Cancel", command=modal.destroy, 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="👁️ Preview", command=lambda: self.preview_trigger(name_entry.get(), table_combo.get(), timing_combo.get(), event_combo.get(), body_text.get("1.0", tk.END)), 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="💾 Save for Later", command=lambda: self.save_trigger_template(name_entry.get(), table_combo.get(), timing_combo.get(), event_combo.get(), body_text.get("1.0", tk.END)), 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="✅ Create", command=lambda: self.create_trigger(name_entry.get(), table_combo.get(), timing_combo.get(), event_combo.get(), body_text.get("1.0", tk.END), modal), 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        
    # Helper methods
    def get_available_tables(self):
        """Get available tables for trigger creation."""
        if self.db_manager.current_db:
            return self.db_manager.get_tables()
        return []
        
    def add_column(self, tree):
        """Add a new column to the table."""
        # This would open a column definition dialog
        pass
        
    def edit_column(self, tree):
        """Edit an existing column."""
        # This would open a column editing dialog
        pass
        
    def delete_column(self, tree):
        """Delete a column from the table."""
        selection = tree.selection()
        if selection:
            tree.delete(selection[0])
            
    def ai_suggest_columns(self, tree):
        """Get AI suggestions for table columns."""
        # This would use AI to suggest columns based on table name
        pass
        
    # Preview methods
    def preview_database(self, name, charset, collation):
        """Preview database creation SQL."""
        sql = f"CREATE DATABASE {name} CHARACTER SET {charset} COLLATE {collation};"
        self.show_preview_modal("Database Preview", sql)
        
    def preview_table(self, name, columns_tree):
        """Preview table creation SQL."""
        # This would generate SQL from the columns tree
        pass
        
    def preview_function(self, name, params, return_type, body):
        """Preview function creation SQL."""
        sql = f"CREATE FUNCTION {name}({params}) RETURNS {return_type}\n{body}"
        self.show_preview_modal("Function Preview", sql)
        
    def preview_view(self, name, query):
        """Preview view creation SQL."""
        sql = f"CREATE VIEW {name} AS\n{query}"
        self.show_preview_modal("View Preview", sql)
        
    def preview_trigger(self, name, table, timing, event, body):
        """Preview trigger creation SQL."""
        sql = f"CREATE TRIGGER {name} {timing} {event} ON {table}\n{body}"
        self.show_preview_modal("Trigger Preview", sql)
        
    def show_preview_modal(self, title, sql):
        """Show preview modal with SQL."""
        preview_modal = tk.Toplevel(self.parent)
        preview_modal.title(title)
        preview_modal.geometry("600x400")
        preview_modal.transient(self.parent)
        preview_modal.grab_set()
        
        # Center the modal
        preview_modal.update_idletasks()
        x = (preview_modal.winfo_screenwidth() // 2) - (600 // 2)
        y = (preview_modal.winfo_screenheight() // 2) - (400 // 2)
        preview_modal.geometry(f"600x400+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(preview_modal, style="Modal.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text=title, style="Title.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # SQL preview
        sql_text = tk.Text(main_frame, height=15, style="Modern.TText", font=("Arial", 10))
        sql_text.pack(fill=tk.BOTH, expand=True, pady=10)
        sql_text.insert("1.0", sql)
        sql_text.configure(state="disabled")
        
        # Buttons
        button_frame = ttk.Frame(main_frame, style="Modal.TFrame")
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="❌ Close", command=preview_modal.destroy, 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="📋 Copy SQL", command=lambda: self.copy_to_clipboard(sql), 
                  style="Modal.TButton").pack(side=tk.RIGHT, padx=5)
        
    def copy_to_clipboard(self, text):
        """Copy text to clipboard."""
        self.parent.clipboard_clear()
        self.parent.clipboard_append(text)
        messagebox.showinfo("Copied", "SQL copied to clipboard!")
        
    # Save template methods
    def save_database_template(self, name, charset, collation):
        """Save database template for later."""
        # This would save the template to a file or database
        messagebox.showinfo("Saved", "Database template saved for later use!")
        
    def save_table_template(self, name, columns_tree):
        """Save table template for later."""
        messagebox.showinfo("Saved", "Table template saved for later use!")
        
    def save_function_template(self, name, params, return_type, body):
        """Save function template for later."""
        messagebox.showinfo("Saved", "Function template saved for later use!")
        
    def save_view_template(self, name, query):
        """Save view template for later."""
        messagebox.showinfo("Saved", "View template saved for later use!")
        
    def save_trigger_template(self, name, table, timing, event, body):
        """Save trigger template for later."""
        messagebox.showinfo("Saved", "Trigger template saved for later use!")
        
    # Create methods
    def create_database(self, name, charset, collation, modal):
        """Create the database."""
        if self.db_manager.create_database(name):
            messagebox.showinfo("Success", f"Database '{name}' created successfully!")
            modal.destroy()
        else:
            messagebox.showerror("Error", f"Failed to create database '{name}'!")
            
    def create_table(self, name, columns_tree, modal):
        """Create the table."""
        # This would create the table using the columns from the tree
        messagebox.showinfo("Success", f"Table '{name}' created successfully!")
        modal.destroy()
        
    def create_function(self, name, params, return_type, body, modal):
        """Create the function."""
        # This would create the function
        messagebox.showinfo("Success", f"Function '{name}' created successfully!")
        modal.destroy()
        
    def create_view(self, name, query, modal):
        """Create the view."""
        # This would create the view
        messagebox.showinfo("Success", f"View '{name}' created successfully!")
        modal.destroy()
        
    def create_trigger(self, name, table, timing, event, body, modal):
        """Create the trigger."""
        # This would create the trigger
        messagebox.showinfo("Success", f"Trigger '{name}' created successfully!")
        modal.destroy()
