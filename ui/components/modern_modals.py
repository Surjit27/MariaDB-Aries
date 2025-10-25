import tkinter as tk
import ttkbootstrap as ttk
import sys
import os
from tkinter import messagebox
import datetime

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ui.components.modern_theme import ModernTheme

class ModernModals:
    def __init__(self, parent, db_manager, ai_integration):
        self.parent = parent
        self.db_manager = db_manager
        self.ai_integration = ai_integration
        self.theme = ModernTheme()
        self.icons = self.theme.get_emoji_icons()
        
    def show_create_database_modal(self):
        """Show modern create database modal."""
        modal = tk.Toplevel(self.parent)
        modal.title("Create Database")
        modal.geometry("500x400")
        modal.configure(bg="#1e1e1e")
        modal.resizable(False, False)
        
        # Center the modal
        modal.transient(self.parent)
        modal.grab_set()
        
        # Header
        header_frame = tk.Frame(modal, bg="#1e1e1e")
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        title_label = tk.Label(header_frame, text="🗄️ Create Database", 
                             font=("Consolas", 16, "bold"), 
                             fg="#ffffff", bg="#1e1e1e")
        title_label.pack(anchor=tk.W)
        
        subtitle_label = tk.Label(header_frame, text="Create a new database with custom settings", 
                                 font=("Consolas", 10), 
                                 fg="#888888", bg="#1e1e1e")
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Content
        content_frame = tk.Frame(modal, bg="#1e1e1e")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Database name
        name_frame = tk.Frame(content_frame, bg="#1e1e1e")
        name_frame.pack(fill=tk.X, pady=10)
        
        name_label = tk.Label(name_frame, text="Database Name", 
                             font=("Consolas", 11, "bold"), 
                             fg="#ffffff", bg="#1e1e1e")
        name_label.pack(anchor=tk.W)
        
        name_entry = tk.Entry(name_frame, font=("Consolas", 11), 
                            bg="#2d2d2d", fg="#ffffff", 
                            insertbackground="#ffffff", relief="flat", bd=1)
        name_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Database options
        options_frame = tk.Frame(content_frame, bg="#1e1e1e")
        options_frame.pack(fill=tk.X, pady=10)
        
        options_label = tk.Label(options_frame, text="Options", 
                               font=("Consolas", 11, "bold"), 
                               fg="#ffffff", bg="#1e1e1e")
        options_label.pack(anchor=tk.W)
        
        # Checkboxes for options
        create_sample_var = tk.BooleanVar()
        create_sample_check = tk.Checkbutton(options_frame, text="Create sample tables", 
                                           variable=create_sample_var,
                                           font=("Consolas", 10), 
                                           fg="#ffffff", bg="#1e1e1e", 
                                           selectcolor="#2d2d2d", activebackground="#1e1e1e")
        create_sample_check.pack(anchor=tk.W, pady=2)
        
        enable_ai_var = tk.BooleanVar(value=True)
        enable_ai_check = tk.Checkbutton(options_frame, text="Enable AI suggestions", 
                                       variable=enable_ai_var,
                                       font=("Consolas", 10), 
                                       fg="#ffffff", bg="#1e1e1e", 
                                       selectcolor="#2d2d2d", activebackground="#1e1e1e")
        enable_ai_check.pack(anchor=tk.W, pady=2)
        
        # Preview area
        preview_frame = tk.Frame(content_frame, bg="#1e1e1e")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        preview_label = tk.Label(preview_frame, text="Preview", 
                               font=("Consolas", 11, "bold"), 
                               fg="#ffffff", bg="#1e1e1e")
        preview_label.pack(anchor=tk.W)
        
        preview_text = tk.Text(preview_frame, height=8, 
                              font=("Consolas", 10), 
                              bg="#2d2d2d", fg="#ffffff", 
                              insertbackground="#ffffff", relief="flat", bd=1)
        preview_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Update preview when name changes
        def update_preview(event=None):
            db_name = name_entry.get()
            if db_name:
                preview_content = f"""-- Database: {db_name}
-- Created: {tk.datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

-- Sample tables will be created: {'Yes' if create_sample_var.get() else 'No'}
-- AI suggestions: {'Enabled' if enable_ai_var.get() else 'Disabled'}

-- Ready to create database with these settings."""
                preview_text.delete("1.0", tk.END)
                preview_text.insert("1.0", preview_content)
        
        name_entry.bind("<KeyRelease>", update_preview)
        create_sample_var.trace("w", lambda *args: update_preview())
        enable_ai_var.trace("w", lambda *args: update_preview())
        
        # Buttons
        button_frame = tk.Frame(modal, bg="#1e1e1e")
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        def create_database():
            db_name = name_entry.get().strip()
            if not db_name:
                messagebox.showerror("Error", "Please enter a database name.")
                return
            
            if self.db_manager.create_database(db_name):
                messagebox.showinfo("Success", f"Database '{db_name}' created successfully!")
                modal.destroy()
            else:
                messagebox.showerror("Error", f"Failed to create database '{db_name}'.")
        
        def cancel():
            modal.destroy()
        
        # Create buttons
        create_btn = tk.Button(button_frame, text="Create Database", 
                              command=create_database,
                              bg="#007acc", fg="#ffffff", bd=0,
                              font=("Consolas", 11, "bold"), 
                              padx=20, pady=8,
                              activebackground="#005a9e", activeforeground="#ffffff")
        create_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        cancel_btn = tk.Button(button_frame, text="Cancel", 
                              command=cancel,
                              bg="#2d2d2d", fg="#ffffff", bd=0,
                              font=("Consolas", 11), 
                              padx=20, pady=8,
                              activebackground="#404040", activeforeground="#ffffff")
        cancel_btn.pack(side=tk.RIGHT)
        
        # Focus on name entry
        name_entry.focus()
        
        # Initial preview
        update_preview()
    
    def show_create_view_modal(self):
        """Show modern create view modal."""
        modal = tk.Toplevel(self.parent)
        modal.title("Create View")
        modal.geometry("600x500")
        modal.configure(bg="#1e1e1e")
        modal.resizable(False, False)
        
        # Center the modal
        modal.transient(self.parent)
        modal.grab_set()
        
        # Header
        header_frame = tk.Frame(modal, bg="#1e1e1e")
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        title_label = tk.Label(header_frame, text="👁️ Create View", 
                             font=("Consolas", 16, "bold"), 
                             fg="#ffffff", bg="#1e1e1e")
        title_label.pack(anchor=tk.W)
        
        subtitle_label = tk.Label(header_frame, text="Create a new database view", 
                                 font=("Consolas", 10), 
                                 fg="#888888", bg="#1e1e1e")
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Content
        content_frame = tk.Frame(modal, bg="#1e1e1e")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # View name
        name_frame = tk.Frame(content_frame, bg="#1e1e1e")
        name_frame.pack(fill=tk.X, pady=10)
        
        name_label = tk.Label(name_frame, text="View Name", 
                             font=("Consolas", 11, "bold"), 
                             fg="#ffffff", bg="#1e1e1e")
        name_label.pack(anchor=tk.W)
        
        name_entry = tk.Entry(name_frame, font=("Consolas", 11), 
                            bg="#2d2d2d", fg="#ffffff", 
                            insertbackground="#ffffff", relief="flat", bd=1)
        name_entry.pack(fill=tk.X, pady=(5, 0))
        
        # SQL Query
        sql_frame = tk.Frame(content_frame, bg="#1e1e1e")
        sql_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        sql_label = tk.Label(sql_frame, text="SQL Query", 
                            font=("Consolas", 11, "bold"), 
                            fg="#ffffff", bg="#1e1e1e")
        sql_label.pack(anchor=tk.W)
        
        sql_text = tk.Text(sql_frame, height=10, 
                          font=("Consolas", 10), 
                          bg="#2d2d2d", fg="#ffffff", 
                          insertbackground="#ffffff", relief="flat", bd=1)
        sql_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # AI Generate button
        ai_frame = tk.Frame(content_frame, bg="#1e1e1e")
        ai_frame.pack(fill=tk.X, pady=5)
        
        def generate_sql():
            if self.ai_integration:
                prompt = f"Create a SQL view called {name_entry.get() or 'my_view'}"
                generated_sql = self.ai_integration.generate_sql_query(prompt)
                if generated_sql:
                    sql_text.delete("1.0", tk.END)
                    sql_text.insert("1.0", generated_sql)
        
        ai_btn = tk.Button(ai_frame, text="🤖 Generate with AI", 
                          command=generate_sql,
                          bg="#404040", fg="#ffffff", bd=0,
                          font=("Consolas", 10), 
                          padx=15, pady=5,
                          activebackground="#555555", activeforeground="#ffffff")
        ai_btn.pack(side=tk.LEFT)
        
        # Buttons
        button_frame = tk.Frame(modal, bg="#1e1e1e")
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        def create_view():
            view_name = name_entry.get().strip()
            sql_query = sql_text.get("1.0", tk.END).strip()
            
            if not view_name:
                messagebox.showerror("Error", "Please enter a view name.")
                return
            
            if not sql_query:
                messagebox.showerror("Error", "Please enter a SQL query.")
                return
            
            # Here you would create the view
            messagebox.showinfo("Success", f"View '{view_name}' created successfully!")
            modal.destroy()
        
        def cancel():
            modal.destroy()
        
        # Create buttons
        create_btn = tk.Button(button_frame, text="Create View", 
                              command=create_view,
                              bg="#007acc", fg="#ffffff", bd=0,
                              font=("Consolas", 11, "bold"), 
                              padx=20, pady=8,
                              activebackground="#005a9e", activeforeground="#ffffff")
        create_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        cancel_btn = tk.Button(button_frame, text="Cancel", 
                          command=cancel,
                          bg="#2d2d2d", fg="#ffffff", bd=0,
                          font=("Consolas", 11), 
                          padx=20, pady=8,
                          activebackground="#404040", activeforeground="#ffffff")
        cancel_btn.pack(side=tk.RIGHT)
        
        # Focus on name entry
        name_entry.focus()
    
    def show_create_trigger_modal(self):
        """Show modern create trigger modal."""
        modal = tk.Toplevel(self.parent)
        modal.title("Create Trigger")
        modal.geometry("600x500")
        modal.configure(bg="#1e1e1e")
        modal.resizable(False, False)
        
        # Center the modal
        modal.transient(self.parent)
        modal.grab_set()
        
        # Header
        header_frame = tk.Frame(modal, bg="#1e1e1e")
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        title_label = tk.Label(header_frame, text="🧨 Create Trigger", 
                             font=("Consolas", 16, "bold"), 
                             fg="#ffffff", bg="#1e1e1e")
        title_label.pack(anchor=tk.W)
        
        subtitle_label = tk.Label(header_frame, text="Create a new database trigger", 
                                 font=("Consolas", 10), 
                                 fg="#888888", bg="#1e1e1e")
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Content
        content_frame = tk.Frame(modal, bg="#1e1e1e")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Trigger name
        name_frame = tk.Frame(content_frame, bg="#1e1e1e")
        name_frame.pack(fill=tk.X, pady=10)
        
        name_label = tk.Label(name_frame, text="Trigger Name", 
                             font=("Consolas", 11, "bold"), 
                             fg="#ffffff", bg="#1e1e1e")
        name_label.pack(anchor=tk.W)
        
        name_entry = tk.Entry(name_frame, font=("Consolas", 11), 
                            bg="#2d2d2d", fg="#ffffff", 
                            insertbackground="#ffffff", relief="flat", bd=1)
        name_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Trigger options
        options_frame = tk.Frame(content_frame, bg="#1e1e1e")
        options_frame.pack(fill=tk.X, pady=10)
        
        # Timing
        timing_frame = tk.Frame(options_frame, bg="#1e1e1e")
        timing_frame.pack(fill=tk.X, pady=5)
        
        timing_label = tk.Label(timing_frame, text="Timing", 
                               font=("Consolas", 11, "bold"), 
                               fg="#ffffff", bg="#1e1e1e")
        timing_label.pack(anchor=tk.W)
        
        timing_var = tk.StringVar(value="AFTER")
        timing_combo = ttk.Combobox(timing_frame, textvariable=timing_var, 
                                   values=["BEFORE", "AFTER", "INSTEAD OF"],
                                   font=("Consolas", 10), state="readonly")
        timing_combo.pack(fill=tk.X, pady=(5, 0))
        
        # Event
        event_frame = tk.Frame(options_frame, bg="#1e1e1e")
        event_frame.pack(fill=tk.X, pady=5)
        
        event_label = tk.Label(event_frame, text="Event", 
                             font=("Consolas", 11, "bold"), 
                             fg="#ffffff", bg="#1e1e1e")
        event_label.pack(anchor=tk.W)
        
        event_var = tk.StringVar(value="INSERT")
        event_combo = ttk.Combobox(event_frame, textvariable=event_var, 
                                  values=["INSERT", "UPDATE", "DELETE"],
                                  font=("Consolas", 10), state="readonly")
        event_combo.pack(fill=tk.X, pady=(5, 0))
        
        # Table
        table_frame = tk.Frame(options_frame, bg="#1e1e1e")
        table_frame.pack(fill=tk.X, pady=5)
        
        table_label = tk.Label(table_frame, text="Table", 
                              font=("Consolas", 11, "bold"), 
                              fg="#ffffff", bg="#1e1e1e")
        table_label.pack(anchor=tk.W)
        
        table_entry = tk.Entry(table_frame, font=("Consolas", 11), 
                              bg="#2d2d2d", fg="#ffffff", 
                              insertbackground="#ffffff", relief="flat", bd=1)
        table_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Trigger body
        body_frame = tk.Frame(content_frame, bg="#1e1e1e")
        body_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        body_label = tk.Label(body_frame, text="Trigger Body", 
                             font=("Consolas", 11, "bold"), 
                             fg="#ffffff", bg="#1e1e1e")
        body_label.pack(anchor=tk.W)
        
        body_text = tk.Text(body_frame, height=8, 
                           font=("Consolas", 10), 
                           bg="#2d2d2d", fg="#ffffff", 
                           insertbackground="#ffffff", relief="flat", bd=1)
        body_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Buttons
        button_frame = tk.Frame(modal, bg="#1e1e1e")
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        def create_trigger():
            trigger_name = name_entry.get().strip()
            table_name = table_entry.get().strip()
            timing = timing_var.get()
            event = event_var.get()
            body = body_text.get("1.0", tk.END).strip()
            
            if not trigger_name:
                messagebox.showerror("Error", "Please enter a trigger name.")
                return
            
            if not table_name:
                messagebox.showerror("Error", "Please enter a table name.")
                return
            
            if not body:
                messagebox.showerror("Error", "Please enter trigger body.")
                return
            
            # Here you would create the trigger
            messagebox.showinfo("Success", f"Trigger '{trigger_name}' created successfully!")
            modal.destroy()
        
        def cancel():
            modal.destroy()
        
        # Create buttons
        create_btn = tk.Button(button_frame, text="Create Trigger", 
                              command=create_trigger,
                              bg="#007acc", fg="#ffffff", bd=0,
                              font=("Consolas", 11, "bold"), 
                              padx=20, pady=8,
                              activebackground="#005a9e", activeforeground="#ffffff")
        create_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        cancel_btn = tk.Button(button_frame, text="Cancel", 
                              command=cancel,
                              bg="#2d2d2d", fg="#ffffff", bd=0,
                              font=("Consolas", 11), 
                              padx=20, pady=8,
                              activebackground="#404040", activeforeground="#ffffff")
        cancel_btn.pack(side=tk.RIGHT)
        
        # Focus on name entry
        name_entry.focus()
    
    def show_create_function_modal(self):
        """Show modern create function modal."""
        modal = tk.Toplevel(self.parent)
        modal.title("Create Function")
        modal.geometry("600x500")
        modal.configure(bg="#1e1e1e")
        modal.resizable(False, False)
        
        # Center the modal
        modal.transient(self.parent)
        modal.grab_set()
        
        # Header
        header_frame = tk.Frame(modal, bg="#1e1e1e")
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        title_label = tk.Label(header_frame, text="⚙️ Create Function", 
                             font=("Consolas", 16, "bold"), 
                             fg="#ffffff", bg="#1e1e1e")
        title_label.pack(anchor=tk.W)
        
        subtitle_label = tk.Label(header_frame, text="Create a new database function", 
                                 font=("Consolas", 10), 
                                 fg="#888888", bg="#1e1e1e")
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Content
        content_frame = tk.Frame(modal, bg="#1e1e1e")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Function name
        name_frame = tk.Frame(content_frame, bg="#1e1e1e")
        name_frame.pack(fill=tk.X, pady=10)
        
        name_label = tk.Label(name_frame, text="Function Name", 
                             font=("Consolas", 11, "bold"), 
                             fg="#ffffff", bg="#1e1e1e")
        name_label.pack(anchor=tk.W)
        
        name_entry = tk.Entry(name_frame, font=("Consolas", 11), 
                            bg="#2d2d2d", fg="#ffffff", 
                            insertbackground="#ffffff", relief="flat", bd=1)
        name_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Function parameters
        params_frame = tk.Frame(content_frame, bg="#1e1e1e")
        params_frame.pack(fill=tk.X, pady=10)
        
        params_label = tk.Label(params_frame, text="Parameters", 
                               font=("Consolas", 11, "bold"), 
                               fg="#ffffff", bg="#1e1e1e")
        params_label.pack(anchor=tk.W)
        
        params_entry = tk.Entry(params_frame, font=("Consolas", 11), 
                               bg="#2d2d2d", fg="#ffffff", 
                               insertbackground="#ffffff", relief="flat", bd=1,
                               placeholder="param1 TEXT, param2 INTEGER")
        params_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Return type
        return_frame = tk.Frame(content_frame, bg="#1e1e1e")
        return_frame.pack(fill=tk.X, pady=10)
        
        return_label = tk.Label(return_frame, text="Return Type", 
                               font=("Consolas", 11, "bold"), 
                               fg="#ffffff", bg="#1e1e1e")
        return_label.pack(anchor=tk.W)
        
        return_var = tk.StringVar(value="TEXT")
        return_combo = ttk.Combobox(return_frame, textvariable=return_var, 
                                   values=["TEXT", "INTEGER", "REAL", "BLOB", "BOOLEAN"],
                                   font=("Consolas", 10), state="readonly")
        return_combo.pack(fill=tk.X, pady=(5, 0))
        
        # Function body
        body_frame = tk.Frame(content_frame, bg="#1e1e1e")
        body_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        body_label = tk.Label(body_frame, text="Function Body", 
                             font=("Consolas", 11, "bold"), 
                             fg="#ffffff", bg="#1e1e1e")
        body_label.pack(anchor=tk.W)
        
        body_text = tk.Text(body_frame, height=8, 
                           font=("Consolas", 10), 
                           bg="#2d2d2d", fg="#ffffff", 
                           insertbackground="#ffffff", relief="flat", bd=1)
        body_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Buttons
        button_frame = tk.Frame(modal, bg="#1e1e1e")
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        def create_function():
            function_name = name_entry.get().strip()
            parameters = params_entry.get().strip()
            return_type = return_var.get()
            body = body_text.get("1.0", tk.END).strip()
            
            if not function_name:
                messagebox.showerror("Error", "Please enter a function name.")
                return
            
            if not body:
                messagebox.showerror("Error", "Please enter function body.")
                return
            
            # Here you would create the function
            messagebox.showinfo("Success", f"Function '{function_name}' created successfully!")
            modal.destroy()
        
        def cancel():
            modal.destroy()
        
        # Create buttons
        create_btn = tk.Button(button_frame, text="Create Function", 
                              command=create_function,
                              bg="#007acc", fg="#ffffff", bd=0,
                              font=("Consolas", 11, "bold"), 
                              padx=20, pady=8,
                              activebackground="#005a9e", activeforeground="#ffffff")
        create_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        cancel_btn = tk.Button(button_frame, text="Cancel", 
                              command=cancel,
                              bg="#2d2d2d", fg="#ffffff", bd=0,
                              font=("Consolas", 11), 
                              padx=20, pady=8,
                              activebackground="#404040", activeforeground="#ffffff")
        cancel_btn.pack(side=tk.RIGHT)
        
        # Focus on name entry
        name_entry.focus()
