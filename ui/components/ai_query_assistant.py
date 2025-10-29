"""
AI Query Assistant - Right-click context menu with full AI pipeline integration
"""

import tkinter as tk
import ttkbootstrap as ttk
from typing import Optional, List
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai.ai_pipeline import AIPipeline


class AIQueryAssistant:
    """AI Query Assistant with table selection and query generation."""
    
    def __init__(self, parent, db_manager, ai_pipeline: AIPipeline, sql_editor):
        self.parent = parent
        self.db_manager = db_manager
        self.ai_pipeline = ai_pipeline
        self.sql_editor = sql_editor
        self.session_id = None
        self.selected_tables = []
        self.assistant_window = None
        
    def show_assistant(self, x: int, y: int, current_query: str = None):
        """Show AI Query Assistant at specified position."""
        
        if not self.ai_pipeline.is_available():
            from tkinter import messagebox
            messagebox.showerror("AI Not Available", 
                               "AI integration is not available. Please check your API key.")
            return
        
        # Check if database is selected
        if not self.db_manager.current_db:
            from tkinter import messagebox
            messagebox.showwarning("No Database Selected", 
                                 "Please select a database first before using AI assistant.")
            return
        
        # Close existing window if open
        if self.assistant_window and self.assistant_window.winfo_exists():
            self.assistant_window.destroy()
        
        # Create AI assistant window
        self.assistant_window = tk.Toplevel(self.parent)
        self.assistant_window.title("🤖 AI Query Assistant")
        self.assistant_window.geometry("900x700")
        self.assistant_window.configure(bg="#1e1e1e")
        
        # Make it modal
        self.assistant_window.transient(self.parent)
        self.assistant_window.grab_set()
        
        # Center the window
        self.assistant_window.update_idletasks()
        x_pos = (self.assistant_window.winfo_screenwidth() // 2) - (self.assistant_window.winfo_width() // 2)
        y_pos = (self.assistant_window.winfo_screenheight() // 2) - (self.assistant_window.winfo_height() // 2)
        self.assistant_window.geometry(f"+{x_pos}+{y_pos}")
        
        # Create UI
        self.create_assistant_ui(current_query)
        
    def create_assistant_ui(self, current_query: str = None):
        """Create the AI assistant interface."""
        
        # Header
        header_frame = tk.Frame(self.assistant_window, bg="#1e1e1e")
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        title_label = tk.Label(header_frame, text="🤖 AI Query Assistant", 
                              font=("Arial", 16, "bold"), fg="#ffffff", bg="#1e1e1e")
        title_label.pack(side=tk.LEFT)
        
        db_label = tk.Label(header_frame, 
                           text=f"Database: {self.db_manager.current_db}", 
                           font=("Arial", 10), fg="#00ff00", bg="#1e1e1e")
        db_label.pack(side=tk.RIGHT)
        
        # Main container
        main_frame = tk.Frame(self.assistant_window, bg="#1e1e1e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left panel - Table selection
        left_panel = tk.Frame(main_frame, bg="#2d2d2d", relief="raised", bd=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5), pady=5)
        left_panel.config(width=250)
        
        # Table selection header
        table_header = tk.Label(left_panel, text="📊 Attach Tables", 
                               font=("Arial", 12, "bold"), fg="#ffffff", bg="#2d2d2d")
        table_header.pack(padx=5, pady=5)
        
        # Info label
        info_label = tk.Label(left_panel, 
                            text="Select tables to provide context\n(like attaching files in Cursor)", 
                            font=("Arial", 9), fg="#888888", bg="#2d2d2d", justify=tk.LEFT)
        info_label.pack(padx=5, pady=(0, 5))
        
        # Table list
        table_frame = tk.Frame(left_panel, bg="#2d2d2d")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar for tables
        table_scrollbar = ttk.Scrollbar(table_frame)
        table_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox with checkboxes (using Listbox with selectmode=MULTIPLE)
        self.table_listbox = tk.Listbox(table_frame, 
                                        selectmode=tk.MULTIPLE,
                                        font=("Consolas", 10),
                                        bg="#1e1e1e", fg="#ffffff",
                                        selectbackground="#007acc",
                                        selectforeground="#ffffff",
                                        yscrollcommand=table_scrollbar.set)
        self.table_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        table_scrollbar.config(command=self.table_listbox.yview)
        
        # Load tables
        self.load_tables()
        
        # Select/Deselect all buttons
        button_frame = tk.Frame(left_panel, bg="#2d2d2d")
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        select_all_btn = tk.Button(button_frame, text="Select All", 
                                   command=self.select_all_tables,
                                   bg="#404040", fg="#ffffff", bd=0,
                                   font=("Arial", 9))
        select_all_btn.pack(side=tk.LEFT, padx=2)
        
        deselect_all_btn = tk.Button(button_frame, text="Clear", 
                                     command=self.deselect_all_tables,
                                     bg="#404040", fg="#ffffff", bd=0,
                                     font=("Arial", 9))
        deselect_all_btn.pack(side=tk.LEFT, padx=2)
        
        # Right panel - Chat and query
        right_panel = tk.Frame(main_frame, bg="#2d2d2d", relief="raised", bd=1)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        
        # Query mode selection
        mode_frame = tk.Frame(right_panel, bg="#2d2d2d")
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        mode_label = tk.Label(mode_frame, text="Mode:", 
                             font=("Arial", 10, "bold"), fg="#ffffff", bg="#2d2d2d")
        mode_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.mode_var = tk.StringVar(value="new")
        
        # Mode radio buttons
        modes = [
            ("new", "🆕 Generate New Query", "Start fresh with a new SQL query"),
            ("modify", "✏️ Modify Existing", "Modify the query in the editor"),
            ("append", "➕ Append to Query", "Add to the end of current query")
        ]
        
        for value, text, tooltip in modes:
            rb = tk.Radiobutton(mode_frame, text=text, variable=self.mode_var, value=value,
                               font=("Arial", 9), fg="#ffffff", bg="#2d2d2d",
                               selectcolor="#007acc", activebackground="#2d2d2d",
                               activeforeground="#ffffff")
            rb.pack(side=tk.LEFT, padx=5)
            self.create_tooltip(rb, tooltip)
        
        # Current query display (if modifying/appending)
        if current_query:
            current_frame = tk.Frame(right_panel, bg="#2d2d2d")
            current_frame.pack(fill=tk.X, padx=5, pady=5)
            
            current_label = tk.Label(current_frame, text="📝 Current Query in Editor:", 
                                    font=("Arial", 10, "bold"), fg="#ffffff", bg="#2d2d2d")
            current_label.pack(anchor=tk.W)
            
            current_text = tk.Text(current_frame, height=4, wrap=tk.WORD,
                                  font=("Consolas", 9), bg="#1e1e1e", fg="#888888",
                                  relief="flat", bd=1)
            current_text.pack(fill=tk.X, pady=(5, 0))
            current_text.insert("1.0", current_query)
            current_text.config(state=tk.DISABLED)
        
        # Chat/Prompt area
        chat_frame = tk.Frame(right_panel, bg="#2d2d2d")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        chat_label = tk.Label(chat_frame, text="💬 Describe what you want:", 
                             font=("Arial", 10, "bold"), fg="#ffffff", bg="#2d2d2d")
        chat_label.pack(anchor=tk.W)
        
        # Chat input
        self.chat_input = tk.Text(chat_frame, height=8, wrap=tk.WORD,
                                 font=("Consolas", 10), bg="#1e1e1e", fg="#ffffff",
                                 insertbackground="#ffffff", relief="flat", bd=1)
        self.chat_input.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Placeholder text
        placeholder = "Example:\n- Show all customers who bought more than $1000\n- Add a filter for orders in 2023\n- Group results by category\n\nYou can also use Tamil, Hindi, or any other language!"
        self.chat_input.insert("1.0", placeholder)
        self.chat_input.config(fg="#666666")
        
        # Bind events for placeholder
        self.chat_input.bind("<FocusIn>", self.clear_placeholder)
        self.chat_input.bind("<FocusOut>", self.restore_placeholder)
        
        # Result display area
        result_frame = tk.Frame(right_panel, bg="#2d2d2d")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        result_label = tk.Label(result_frame, text="✨ Generated Query:", 
                               font=("Arial", 10, "bold"), fg="#ffffff", bg="#2d2d2d")
        result_label.pack(anchor=tk.W)
        
        # Result text area
        result_container = tk.Frame(result_frame, bg="#2d2d2d")
        result_container.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        result_scrollbar = ttk.Scrollbar(result_container)
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.result_text = tk.Text(result_container, height=10, wrap=tk.WORD,
                                  font=("Consolas", 10), bg="#1e1e1e", fg="#00ff00",
                                  relief="flat", bd=1, state=tk.DISABLED,
                                  yscrollcommand=result_scrollbar.set)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        result_scrollbar.config(command=self.result_text.yview)
        
        # Bottom button frame
        bottom_frame = tk.Frame(self.assistant_window, bg="#1e1e1e")
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Left side - status
        self.status_label = tk.Label(bottom_frame, text="Ready to generate query", 
                                     font=("Arial", 9), fg="#888888", bg="#1e1e1e")
        self.status_label.pack(side=tk.LEFT)
        
        # Right side - action buttons
        button_container = tk.Frame(bottom_frame, bg="#1e1e1e")
        button_container.pack(side=tk.RIGHT)
        
        # Generate button
        generate_btn = tk.Button(button_container, text="🚀 Generate Query", 
                                command=self.generate_query,
                                bg="#28a745", fg="#ffffff", bd=0,
                                font=("Arial", 10, "bold"), padx=20, pady=8,
                                activebackground="#218838", activeforeground="#ffffff")
        generate_btn.pack(side=tk.LEFT, padx=5)
        
        # Keep button (apply to editor)
        self.keep_btn = tk.Button(button_container, text="✅ Keep & Apply", 
                                  command=self.keep_query,
                                  bg="#007acc", fg="#ffffff", bd=0,
                                  font=("Arial", 10, "bold"), padx=20, pady=8,
                                  activebackground="#005a9e", activeforeground="#ffffff",
                                  state=tk.DISABLED)
        self.keep_btn.pack(side=tk.LEFT, padx=5)
        
        # Discard button
        self.discard_btn = tk.Button(button_container, text="❌ Discard", 
                                     command=self.discard_query,
                                     bg="#dc3545", fg="#ffffff", bd=0,
                                     font=("Arial", 10, "bold"), padx=20, pady=8,
                                     activebackground="#c82333", activeforeground="#ffffff",
                                     state=tk.DISABLED)
        self.discard_btn.pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_btn = tk.Button(button_container, text="Close", 
                             command=self.close_assistant,
                             bg="#6c757d", fg="#ffffff", bd=0,
                             font=("Arial", 10), padx=20, pady=8,
                             activebackground="#5a6268", activeforeground="#ffffff")
        close_btn.pack(side=tk.LEFT, padx=5)
    
    def load_tables(self):
        """Load tables from database."""
        try:
            tables = self.db_manager.get_tables()
            self.table_listbox.delete(0, tk.END)
            
            for table in tables:
                # Get row count for display
                try:
                    columns, data = self.db_manager.get_table_data(table, limit=1)
                    row_count = len(data) if data else 0
                    display_text = f"📊 {table} ({row_count} rows)"
                except:
                    display_text = f"📊 {table}"
                
                self.table_listbox.insert(tk.END, display_text)
        except Exception as e:
            print(f"Error loading tables: {e}")
    
    def select_all_tables(self):
        """Select all tables."""
        self.table_listbox.select_set(0, tk.END)
    
    def deselect_all_tables(self):
        """Deselect all tables."""
        self.table_listbox.selection_clear(0, tk.END)
    
    def get_selected_tables(self) -> List[str]:
        """Get list of selected table names."""
        selected_indices = self.table_listbox.curselection()
        tables = []
        
        for idx in selected_indices:
            display_text = self.table_listbox.get(idx)
            # Extract table name (remove emoji and row count)
            table_name = display_text.replace("📊 ", "").split(" (")[0]
            tables.append(table_name)
        
        return tables
    
    def clear_placeholder(self, event):
        """Clear placeholder text on focus."""
        if self.chat_input.get("1.0", tk.END).strip().startswith("Example:"):
            self.chat_input.delete("1.0", tk.END)
            self.chat_input.config(fg="#ffffff")
    
    def restore_placeholder(self, event):
        """Restore placeholder if empty."""
        if not self.chat_input.get("1.0", tk.END).strip():
            placeholder = "Example:\n- Show all customers who bought more than $1000\n- Add a filter for orders in 2023\n- Group results by category\n\nYou can also use Tamil, Hindi, or any other language!"
            self.chat_input.insert("1.0", placeholder)
            self.chat_input.config(fg="#666666")
    
    def generate_query(self):
        """Generate SQL query using AI."""
        # Get user prompt
        user_prompt = self.chat_input.get("1.0", tk.END).strip()
        
        if not user_prompt or user_prompt.startswith("Example:"):
            self.status_label.config(text="❌ Please enter a description", fg="#ff0000")
            return
        
        # Get selected tables
        selected_tables = self.get_selected_tables()
        
        if not selected_tables:
            from tkinter import messagebox
            response = messagebox.askyesno("No Tables Selected", 
                                          "No tables selected. Use entire database schema?")
            if not response:
                return
        
        # Get current query from editor if modifying/appending
        current_query = None
        mode = self.mode_var.get()
        if mode in ["modify", "append"]:
            current_query = self.sql_editor.editor.get("1.0", tk.END).strip()
            if not current_query:
                self.status_label.config(text="❌ No query in editor to modify", fg="#ff0000")
                return
        
        # Update status
        self.status_label.config(text="⏳ Generating query with AI...", fg="#ffa500")
        self.assistant_window.update()
        
        try:
            # Start AI session
            if not self.session_id:
                self.session_id = self.ai_pipeline.start_ai_session(
                    self.db_manager.current_db,
                    selected_tables if selected_tables else None,
                    current_query
                )
            
            # Generate query
            result = self.ai_pipeline.generate_query(
                self.session_id,
                user_prompt,
                action=mode
            )
            
            if result.get('success') and result.get('query'):
                # Display result
                self.display_result(result)
                self.status_label.config(text=f"✅ Query generated (Confidence: {result.get('confidence', 0.9):.0%})", 
                                       fg="#00ff00")
                
                # Enable keep/discard buttons
                self.keep_btn.config(state=tk.NORMAL)
                self.discard_btn.config(state=tk.NORMAL)
            else:
                error_msg = result.get('error', 'Unknown error')
                self.status_label.config(text=f"❌ Error: {error_msg}", fg="#ff0000")
                self.display_error(error_msg)
                
        except Exception as e:
            self.status_label.config(text=f"❌ Error: {str(e)}", fg="#ff0000")
            self.display_error(str(e))
    
    def display_result(self, result: dict):
        """Display generated query and explanation."""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        
        # Insert query
        query = result.get('query', '')
        explanation = result.get('explanation', '')
        confidence = result.get('confidence', 0.9)
        complexity = result.get('complexity', 'Medium')
        changes_made = result.get('changes_made')
        
        # Format output
        output = f"SQL QUERY:\n{'='*50}\n{query}\n\n"
        output += f"EXPLANATION:\n{'-'*50}\n{explanation}\n\n"
        
        if changes_made:
            output += f"CHANGES MADE:\n{'-'*50}\n{changes_made}\n\n"
        
        output += f"METADATA:\n{'-'*50}\n"
        output += f"Confidence: {confidence:.0%}\n"
        output += f"Complexity: {complexity}\n"
        
        self.result_text.insert("1.0", output)
        self.result_text.config(state=tk.DISABLED)
        
        # Store generated query
        self.generated_query = query
    
    def display_error(self, error_msg: str):
        """Display error message."""
        self.result_text.config(state=tk.NORMAL, fg="#ff0000")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", f"❌ ERROR:\n\n{error_msg}")
        self.result_text.config(state=tk.DISABLED)
    
    def keep_query(self):
        """Apply generated query to editor."""
        if hasattr(self, 'generated_query'):
            mode = self.mode_var.get()
            
            if mode == "new":
                # Replace entire editor content
                self.sql_editor.editor.delete("1.0", tk.END)
                self.sql_editor.editor.insert("1.0", self.generated_query)
            elif mode == "modify":
                # Replace entire editor content with modified query
                self.sql_editor.editor.delete("1.0", tk.END)
                self.sql_editor.editor.insert("1.0", self.generated_query)
            elif mode == "append":
                # Append to existing query
                current = self.sql_editor.editor.get("1.0", tk.END).strip()
                if current:
                    self.sql_editor.editor.insert(tk.END, "\n\n" + self.generated_query)
                else:
                    self.sql_editor.editor.insert("1.0", self.generated_query)
            
            self.status_label.config(text="✅ Query applied to editor", fg="#00ff00")
            
            # Close assistant after short delay
            self.assistant_window.after(1000, self.close_assistant)
    
    def discard_query(self):
        """Discard generated query."""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.config(state=tk.DISABLED)
        
        self.keep_btn.config(state=tk.DISABLED)
        self.discard_btn.config(state=tk.DISABLED)
        
        self.status_label.config(text="Query discarded", fg="#888888")
        
        if hasattr(self, 'generated_query'):
            delattr(self, 'generated_query')
    
    def close_assistant(self):
        """Close AI assistant and cleanup."""
        if self.session_id:
            self.ai_pipeline.close_session(self.session_id)
            self.session_id = None
        
        if self.assistant_window:
            self.assistant_window.destroy()
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, 
                           bg="#2d2d2d", fg="#ffffff", 
                           relief="solid", borderwidth=1,
                           font=("Arial", 9), padx=5, pady=3)
            label.pack()
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
