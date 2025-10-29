"""
Horizontal AI Query Assistant Modal - A compact, tooltip-style modal for AI query assistance
"""

import tkinter as tk
import ttkbootstrap as ttk
from typing import Optional, List, Dict, Any
import sys
import os
import re
import time

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ui.components.modern_theme import ModernTheme
from ai.ai_pipeline import AIPipeline


class HorizontalAIModal:
    """
    A compact, horizontal tooltip-style AI modal that appears on demand.
    Features table/column selection with @ and # triggers, conversation history,
    and confirmation prompts before overwriting content.
    """
    
    def __init__(self, parent, ai_integration, sql_editor, db_manager):
        self.parent = parent
        self.ai_integration = ai_integration
        self.sql_editor = sql_editor
        self.db_manager = db_manager
        self.theme = ModernTheme()
        
        # Modal state
        self.modal_window = None
        self.is_visible = False
        self.conversation_history = []
        self.selected_tables = []
        self.selected_columns = {}
        
        # UI components
        self.input_entry = None
        self.history_frame = None
        self.table_dropdown = None
        self.column_dropdown = None
        self.dropdown_window = None
        self.current_dropdown_type = None
        
        # Configuration
        self.modal_width = 800
        self.modal_height = 120
        self.history_height = 200
        self.auto_hide_delay = 10000  # 10 seconds
        
    def show_modal(self, event=None, position=None):
        """Show the horizontal AI modal with smart positioning."""
        if self.is_visible:
            self.hide_modal()
            return
            
        self.is_visible = True
        
        # Calculate position
        if position:
            x, y = position
        elif event:
            x = event.x_root
            y = event.y_root
        else:
            # Default to center of parent window
            x = self.parent.winfo_rootx() + self.parent.winfo_width() // 2 - self.modal_width // 2
            y = self.parent.winfo_rooty() + 50
            
        # Adjust position to avoid screen edges
        x, y = self._adjust_position(x, y)
        
        # Create modal window
        self.modal_window = tk.Toplevel(self.parent)
        self.modal_window.wm_overrideredirect(True)
        self.modal_window.wm_geometry(f"{self.modal_width}x{self.modal_height}+{x}+{y}")
        self.modal_window.configure(bg="#2d2d2d")
        self.modal_window.wm_attributes("-topmost", True)
        self.modal_window.wm_attributes("-alpha", 0.95)
        
        # Prevent modal from losing focus
        self.modal_window.focus_force()
        self.modal_window.grab_set()
        
        # Create main frame with subtle shadow effect
        main_frame = tk.Frame(self.modal_window, bg="#2d2d2d", relief="raised", bd=1)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Create content frame
        content_frame = tk.Frame(main_frame, bg="#2d2d2d")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        
        # Create the horizontal layout
        self.create_horizontal_layout(content_frame)
        
        # Bind events
        self.bind_events()
        
        # Bind click events to SQL editor to remove highlights
        if hasattr(self.sql_editor, 'editor'):
            self.sql_editor.editor.bind("<Button-1>", self.on_editor_click)
            self.sql_editor.editor.bind("<Key>", self.on_editor_key)
        
        # Focus and select text
        self.input_entry.focus()
        self.input_entry.select_range(0, tk.END)
        
    def create_horizontal_layout(self, parent):
        """Create the horizontal layout for the modal."""
        # Top row - Input and controls
        top_frame = tk.Frame(parent, bg="#2d2d2d")
        top_frame.pack(fill=tk.X, pady=(0, 5))
        
        # AI icon
        ai_icon = tk.Label(top_frame, text="🤖", font=("Arial", 12), 
                          bg="#2d2d2d", fg="#ffffff")
        ai_icon.pack(side=tk.LEFT, padx=(0, 8))
        
        # Input entry with @ and # support
        self.input_var = tk.StringVar()
        self.input_var.trace('w', self.on_text_change)
        self.input_entry = tk.Entry(top_frame, 
                                   textvariable=self.input_var,
                                   font=("Consolas", 10),
                                   bg="#404040", fg="#ffffff",
                                   insertbackground="#ffffff",
                                   relief="flat", bd=0,
                                   width=60)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        # Action buttons
        button_frame = tk.Frame(top_frame, bg="#2d2d2d")
        button_frame.pack(side=tk.RIGHT)
        
        # Generate button
        generate_btn = tk.Button(button_frame, text="▶", 
                               command=self.generate_sql,
                               bg="#007acc", fg="#ffffff", bd=0,
                               font=("Arial", 9, "bold"), 
                               width=3, height=1,
                               activebackground="#005a9e", 
                               activeforeground="#ffffff",
                               relief="flat")
        generate_btn.pack(side=tk.LEFT, padx=(0, 3))
        
        # History toggle button
        history_btn = tk.Button(button_frame, text="📜", 
                              command=self.toggle_history,
                              bg="#666666", fg="#ffffff", bd=0,
                              font=("Arial", 9), 
                              width=3, height=1,
                              activebackground="#888888", 
                              activeforeground="#ffffff",
                              relief="flat")
        history_btn.pack(side=tk.LEFT, padx=(0, 3))
        
        # Close button
        close_btn = tk.Button(button_frame, text="✕", 
                            command=self.hide_modal,
                            bg="#dc3545", fg="#ffffff", bd=0,
                            font=("Arial", 9, "bold"), 
                            width=3, height=1,
                            activebackground="#c82333", 
                            activeforeground="#ffffff",
                            relief="flat")
        close_btn.pack(side=tk.LEFT)
        
        # Bottom row - Conversation history (initially hidden)
        self.history_frame = tk.Frame(parent, bg="#2d2d2d")
        # Will be packed when toggled
        
        # Create history content
        self.create_history_content()
        
    def create_history_content(self):
        """Create the conversation history content."""
        if not self.history_frame:
            return
            
        # History header
        history_header = tk.Frame(self.history_frame, bg="#2d2d2d")
        history_header.pack(fill=tk.X, pady=(0, 5))
        
        history_title = tk.Label(history_header, text="💬 Conversation History", 
                               font=("Arial", 9, "bold"), fg="#ffffff", bg="#2d2d2d")
        history_title.pack(side=tk.LEFT)
        
        clear_btn = tk.Button(history_header, text="🗑️ Clear", 
                            command=self.clear_history,
                            bg="#666666", fg="#ffffff", bd=0,
                            font=("Arial", 8), 
                            width=6, height=1,
                            activebackground="#888888", 
                            activeforeground="#ffffff",
                            relief="flat")
        clear_btn.pack(side=tk.RIGHT)
        
        # History scrollable area
        history_container = tk.Frame(self.history_frame, bg="#2d2d2d")
        history_container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        history_scrollbar = ttk.Scrollbar(history_container)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # History text widget
        self.history_text = tk.Text(history_container, 
                                   height=8, wrap=tk.WORD,
                                   font=("Consolas", 9), 
                                   bg="#1e1e1e", fg="#ffffff",
                                   relief="flat", bd=1, state=tk.DISABLED,
                                   yscrollcommand=history_scrollbar.set)
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.config(command=self.history_text.yview)
        
    def bind_events(self):
        """Bind events for the modal."""
        # Input entry events
        self.input_entry.bind("<Return>", lambda e: self.generate_sql())
        self.input_entry.bind("<Escape>", lambda e: self.hide_modal())
        self.input_entry.bind("<KeyPress>", self.on_key_press)
        self.input_entry.bind("<KeyRelease>", self.on_key_release)
        self.input_entry.bind("<FocusIn>", self.on_focus_in)
        self.input_entry.bind("<FocusOut>", self.on_focus_out)
        
        # Modal events
        self.modal_window.bind("<FocusOut>", self.on_modal_focus_out)
        self.modal_window.bind("<Button-1>", self.on_modal_click)
        
    def on_key_press(self, event):
        """Handle key press events for @ and # triggers."""
        char = event.char
        keysym = event.keysym
        print(f"Key pressed: char='{char}', keysym='{keysym}'")  # Debug print
        
        if char == '@' or keysym == 'at':
            # Show table dropdown
            print("Showing table dropdown")  # Debug print
            self.show_table_dropdown()
            return "break"
        elif char == '#' or keysym == 'numbersign':
            # Show column dropdown
            print("Showing column dropdown")  # Debug print
            self.show_column_dropdown()
            return "break"
        elif char == ' ':
            # Hide dropdowns on space
            self.hide_dropdown()
        
        # Allow normal typing
        return
    
    def on_key_release(self, event):
        """Handle key release events."""
        char = event.char
        keysym = event.keysym
        print(f"Key released: char='{char}', keysym='{keysym}'")  # Debug print
        
        # Check for @ and # on key release as well
        if char == '@' or keysym == 'at':
            print("Key release: @ detected")
        elif char == '#' or keysym == 'numbersign':
            print("Key release: # detected")
    
    def on_text_change(self, *args):
        """Handle text changes in the input field."""
        current_text = self.input_var.get()
        print(f"Text changed: '{current_text}'")  # Debug print
        
        # Check if the last character is @ or #
        if current_text.endswith('@'):
            print("Text change: @ detected at end")
            # Small delay to prevent modal from closing
            self.modal_window.after(100, self.show_table_dropdown)
        elif current_text.endswith('#'):
            print("Text change: # detected at end")
            # Small delay to prevent modal from closing
            self.modal_window.after(100, self.show_column_dropdown)
            
    def on_focus_in(self, event):
        """Handle focus in event."""
        pass
        
    def on_focus_out(self, event):
        """Handle focus out event."""
        pass
        
    def on_modal_focus_out(self, event):
        """Handle modal focus out event."""
        # Don't auto-hide on focus out to prevent modal from disappearing
        # User can close with Escape key or close button
        pass
            
    def on_modal_click(self, event):
        """Handle click on modal to prevent auto-hide."""
        pass
        
    def show_table_dropdown(self):
        """Show table selection dropdown."""
        if not self.db_manager.current_db:
            return
            
        # Get cursor position
        cursor_pos = self.input_entry.index(tk.INSERT)
        bbox = self.input_entry.bbox(cursor_pos)
        if bbox is None:
            # Fallback position
            x, y = 0, 0
        else:
            x, y, width, height = bbox
            
        # Create dropdown window
        self.dropdown_window = tk.Toplevel(self.modal_window)
        self.dropdown_window.wm_overrideredirect(True)
        self.dropdown_window.wm_geometry(f"+{self.modal_window.winfo_rootx() + x}+{self.modal_window.winfo_rooty() + y + 25}")
        self.dropdown_window.configure(bg="#2d2d2d")
        self.dropdown_window.wm_attributes("-topmost", True)
        
        # Create dropdown frame
        dropdown_frame = tk.Frame(self.dropdown_window, bg="#2d2d2d", relief="raised", bd=1)
        dropdown_frame.pack()
        
        # Search entry
        search_frame = tk.Frame(dropdown_frame, bg="#2d2d2d")
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        search_entry = tk.Entry(search_frame, 
                               font=("Consolas", 9),
                               bg="#404040", fg="#ffffff",
                               insertbackground="#ffffff",
                               relief="flat", bd=0,
                               width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_entry.bind("<KeyRelease>", lambda e: self.filter_tables(search_entry.get()))
        
        # Table list
        list_frame = tk.Frame(dropdown_frame, bg="#2d2d2d")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Scrollbar
        list_scrollbar = ttk.Scrollbar(list_frame)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox
        self.table_listbox = tk.Listbox(list_frame, 
                                       font=("Consolas", 9),
                                       bg="#1e1e1e", fg="#ffffff",
                                       selectbackground="#007acc",
                                       selectforeground="#ffffff",
                                       yscrollcommand=list_scrollbar.set,
                                       height=8)
        self.table_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.config(command=self.table_listbox.yview)
        
        # Load tables
        self.load_tables()
        
        # Bind selection
        self.table_listbox.bind("<Double-1>", self.select_table)
        self.table_listbox.bind("<Return>", self.select_table)
        
        # Focus search
        search_entry.focus()
        self.current_dropdown_type = "table"
        
    def show_column_dropdown(self):
        """Show column selection dropdown."""
        if not self.db_manager.current_db or not self.selected_tables:
            return
            
        # Get cursor position
        cursor_pos = self.input_entry.index(tk.INSERT)
        bbox = self.input_entry.bbox(cursor_pos)
        if bbox is None:
            # Fallback position
            x, y = 0, 0
        else:
            x, y, width, height = bbox
            
        # Create dropdown window
        self.dropdown_window = tk.Toplevel(self.modal_window)
        self.dropdown_window.wm_overrideredirect(True)
        self.dropdown_window.wm_geometry(f"+{self.modal_window.winfo_rootx() + x}+{self.modal_window.winfo_rooty() + y + 25}")
        self.dropdown_window.configure(bg="#2d2d2d")
        self.dropdown_window.wm_attributes("-topmost", True)
        
        # Create dropdown frame
        dropdown_frame = tk.Frame(self.dropdown_window, bg="#2d2d2d", relief="raised", bd=1)
        dropdown_frame.pack()
        
        # Search entry
        search_frame = tk.Frame(dropdown_frame, bg="#2d2d2d")
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        search_entry = tk.Entry(search_frame, 
                               font=("Consolas", 9),
                               bg="#404040", fg="#ffffff",
                               insertbackground="#ffffff",
                               relief="flat", bd=0,
                               width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_entry.bind("<KeyRelease>", lambda e: self.filter_columns(search_entry.get()))
        
        # Column list
        list_frame = tk.Frame(dropdown_frame, bg="#2d2d2d")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Scrollbar
        list_scrollbar = ttk.Scrollbar(list_frame)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox
        self.column_listbox = tk.Listbox(list_frame, 
                                        font=("Consolas", 9),
                                        bg="#1e1e1e", fg="#ffffff",
                                        selectbackground="#007acc",
                                        selectforeground="#ffffff",
                                        yscrollcommand=list_scrollbar.set,
                                        height=8)
        self.column_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.config(command=self.column_listbox.yview)
        
        # Load columns
        self.load_columns()
        
        # Bind selection
        self.column_listbox.bind("<Double-1>", self.select_column)
        self.column_listbox.bind("<Return>", self.select_column)
        
        # Focus search
        search_entry.focus()
        self.current_dropdown_type = "column"
        
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
            
    def load_columns(self):
        """Load columns from selected tables."""
        try:
            self.column_listbox.delete(0, tk.END)
            
            for table in self.selected_tables:
                try:
                    columns, _ = self.db_manager.get_table_data(table, limit=1)
                    for column in columns:
                        display_text = f"📋 {table}.{column}"
                        self.column_listbox.insert(tk.END, display_text)
                except:
                    pass
        except Exception as e:
            print(f"Error loading columns: {e}")
            
    def filter_tables(self, search_text):
        """Filter tables based on search text."""
        if not search_text:
            self.load_tables()
            return
            
        try:
            tables = self.db_manager.get_tables()
            self.table_listbox.delete(0, tk.END)
            
            for table in tables:
                if search_text.lower() in table.lower():
                    try:
                        columns, data = self.db_manager.get_table_data(table, limit=1)
                        row_count = len(data) if data else 0
                        display_text = f"📊 {table} ({row_count} rows)"
                    except:
                        display_text = f"📊 {table}"
                    
                    self.table_listbox.insert(tk.END, display_text)
        except Exception as e:
            print(f"Error filtering tables: {e}")
            
    def filter_columns(self, search_text):
        """Filter columns based on search text."""
        if not search_text:
            self.load_columns()
            return
            
        try:
            self.column_listbox.delete(0, tk.END)
            
            for table in self.selected_tables:
                try:
                    columns, _ = self.db_manager.get_table_data(table, limit=1)
                    for column in columns:
                        if search_text.lower() in column.lower() or search_text.lower() in table.lower():
                            display_text = f"📋 {table}.{column}"
                            self.column_listbox.insert(tk.END, display_text)
                except:
                    pass
        except Exception as e:
            print(f"Error filtering columns: {e}")
            
    def select_table(self, event=None):
        """Select a table from the dropdown."""
        selection = self.table_listbox.curselection()
        if selection:
            display_text = self.table_listbox.get(selection[0])
            # Extract table name (remove emoji and row count)
            table_name = display_text.replace("📊 ", "").split(" (")[0]
            
            if table_name not in self.selected_tables:
                self.selected_tables.append(table_name)
                
            # Insert @table_name into input
            cursor_pos = self.input_entry.index(tk.INSERT)
            self.input_entry.insert(cursor_pos, f"@{table_name} ")
            
        self.hide_dropdown()
        
    def select_column(self, event=None):
        """Select a column from the dropdown."""
        selection = self.column_listbox.curselection()
        if selection:
            display_text = self.column_listbox.get(selection[0])
            # Extract column name (remove emoji)
            column_name = display_text.replace("📋 ", "")
            
            # Insert #column_name into input
            cursor_pos = self.input_entry.index(tk.INSERT)
            self.input_entry.insert(cursor_pos, f"#{column_name} ")
            
        self.hide_dropdown()
        
    def hide_dropdown(self):
        """Hide the current dropdown."""
        if self.dropdown_window and self.dropdown_window.winfo_exists():
            self.dropdown_window.destroy()
        self.dropdown_window = None
        self.current_dropdown_type = None
        
    def toggle_history(self):
        """Toggle conversation history visibility."""
        if self.history_frame.winfo_ismapped():
            self.history_frame.pack_forget()
            # Resize modal
            self.modal_window.wm_geometry(f"{self.modal_width}x{self.modal_height}")
        else:
            self.history_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
            # Resize modal
            self.modal_window.wm_geometry(f"{self.modal_width}x{self.modal_height + self.history_height}")
            
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        if hasattr(self, 'history_text'):
            self.history_text.config(state=tk.NORMAL)
            self.history_text.delete("1.0", tk.END)
            self.history_text.config(state=tk.DISABLED)
            
    def get_selected_text_from_editor(self):
        """Get selected text from the SQL editor and highlight it."""
        try:
            # Check if there's a selection in the editor
            if hasattr(self.sql_editor, 'editor'):
                selected_text = self.sql_editor.editor.get(tk.SEL_FIRST, tk.SEL_LAST)
                if selected_text:
                    # Highlight the selected text
                    sel_start = self.sql_editor.editor.index(tk.SEL_FIRST)
                    sel_end = self.sql_editor.editor.index(tk.SEL_LAST)
                    self.highlight_selected_text(sel_start, sel_end)
                    return selected_text.strip()
        except tk.TclError:
            # No selection
            pass
        return None
    
    def add_to_history(self, user_input, ai_response):
        """Add interaction to conversation history."""
        self.conversation_history.append({
            'user': user_input,
            'ai': ai_response,
            'timestamp': time.time()
        })
        
        # Update history display
        if hasattr(self, 'history_text'):
            self.history_text.config(state=tk.NORMAL)
            self.history_text.insert(tk.END, f"👤 {user_input}\n")
            self.history_text.insert(tk.END, f"🤖 {ai_response}\n\n")
            self.history_text.see(tk.END)
            self.history_text.config(state=tk.DISABLED)
            
    def generate_sql(self):
        """Generate SQL using AI."""
        prompt = self.input_var.get().strip()
        if not prompt:
            return
            
        # Show loading state
        self.input_entry.configure(state="disabled")
        self.input_var.set("🤖 Generating...")
        self.modal_window.update()
        
        try:
            # Get selected text from SQL editor
            selected_text = self.get_selected_text_from_editor()
            
            # Get database schema for context
            schema = None
            if self.db_manager and self.db_manager.current_db:
                try:
                    tables = self.db_manager.get_tables()
                    # Create proper schema format for AI - tables should be list of dicts
                    table_schemas = []
                    for table_name in tables:
                        try:
                            # Get table columns
                            columns, _ = self.db_manager.get_table_data(table_name, limit=1)
                            table_schema = {
                                "table_name": table_name,
                                "columns": [{"name": col, "type": "TEXT"} for col in columns]
                            }
                            table_schemas.append(table_schema)
                        except:
                            # Fallback if we can't get columns
                            table_schema = {
                                "table_name": table_name,
                                "columns": []
                            }
                            table_schemas.append(table_schema)
                    
                    schema = {
                        "database_name": self.db_manager.current_db,
                        "tables": table_schemas,
                        "relationships": []
                    }
                except:
                    pass
            
            # Generate SQL using AI
            if self.ai_integration:
                # Enhanced prompt to ensure complete queries
                enhanced_prompt = f"""
Generate a complete SQL query for the following request: {prompt}

CRITICAL REQUIREMENTS:
1. Provide a COMPLETE, executable SQL query
2. Include proper syntax and formatting
3. End with semicolon (;)
4. Do NOT truncate or cut off the query
5. If the query is complex, make sure ALL parts are included
6. For CREATE TABLE statements, include ALL columns and constraints
7. For INSERT statements, include ALL values
8. For SELECT statements, include complete WHERE, ORDER BY, GROUP BY clauses if needed

IMPORTANT: Generate the ENTIRE query, do not stop in the middle. The query must be complete and executable.

Database context: {self.db_manager.current_db if self.db_manager.current_db else 'No database selected'}

Generate the complete SQL query now:
"""
                
                generated_sql = self.ai_integration.generate_sql_query(enhanced_prompt, schema)
                if generated_sql:
                    # Debug: Print the generated SQL to see what we're getting
                    print(f"Generated SQL: {repr(generated_sql)}")
                    print(f"SQL length: {len(generated_sql)}")
                    
                    # Check if query looks complete
                    if self.is_query_complete(generated_sql):
                        # Add to history
                        self.add_to_history(prompt, generated_sql)
                        
                        # Show confirmation before applying
                        self.show_confirmation_prompt(generated_sql, selected_text)
                        
                        # Show success
                        self.input_entry.configure(state="normal")
                        self.input_var.set("✅ Generated successfully!")
                        self.modal_window.after(2000, lambda: self.input_var.set(""))
                    else:
                        # Query seems incomplete, try to get more complete version
                        print(f"Incomplete query detected: {repr(generated_sql)}")
                        
                        # If query is very short (less than 50 chars), try again with different prompt
                        if len(generated_sql.strip()) < 50:
                            print("Query too short, trying again with different approach...")
                            self.try_alternative_generation(prompt, schema, selected_text)
                        else:
                            self.handle_incomplete_query(generated_sql, prompt, selected_text)
                else:
                    self._show_error("❌ Failed to generate SQL")
            else:
                self._show_error("❌ AI not available")
        except Exception as e:
            self._show_error(f"❌ Error: {str(e)}")
            
    def show_confirmation_prompt(self, generated_sql, selected_text=None):
        """Show confirmation prompt before overwriting content."""
        if selected_text:
            # There's selected text, replace only that
            from tkinter import messagebox
            response = messagebox.askyesno(
                "Confirm Replace Selection",
                f"Selected text:\n\n{selected_text[:100]}{'...' if len(selected_text) > 100 else ''}\n\nDo you want to replace it with the generated SQL?",
                icon="question"
            )
            
            if response:
                self.replace_selected_text(generated_sql)
            else:
                # User declined, show the SQL in a popup for manual copy
                self.show_sql_popup(generated_sql)
        else:
            # No selection, check if editor has content
            current_content = self.sql_editor.editor.get("1.0", tk.END).strip()
            if not current_content:
                # No content, insert at cursor
                self.insert_at_cursor(generated_sql)
                return
                
            # Show confirmation dialog with options
            from tkinter import messagebox
            response = messagebox.askyesnocancel(
                "Insert Generated SQL",
                f"The editor contains existing content.\n\nHow would you like to insert the generated SQL?",
                detail="Yes: Insert at cursor position\nNo: Replace entire editor\nCancel: Show in popup for manual copy",
                icon="question"
            )
            
            if response is True:  # Yes - insert at cursor
                self.insert_at_cursor(generated_sql)
            elif response is False:  # No - replace entire editor
                self.apply_sql(generated_sql)
            else:  # Cancel - show popup
                self.show_sql_popup(generated_sql)
            
    def apply_sql(self, sql):
        """Apply generated SQL to the editor."""
        self.sql_editor.editor.delete("1.0", tk.END)
        self.sql_editor.editor.insert("1.0", sql)
        
        # Highlight the entire replaced content
        end_pos = self.sql_editor.editor.index(f"1.0+{len(sql)}c")
        self.highlight_replaced_text("1.0", end_pos)
    
    def insert_at_cursor(self, sql):
        """Insert SQL at the current cursor position with proper spacing."""
        cursor_pos = self.sql_editor.editor.index(tk.INSERT)
        
        # Add a newline before the SQL if not at the beginning of a line
        line_start = f"{cursor_pos.split('.')[0]}.0"
        line_content = self.sql_editor.editor.get(line_start, cursor_pos)
        if line_content.strip():  # If there's content on the current line
            sql = "\n" + sql
        
        # Add a newline after the SQL
        sql = sql + "\n"
        
        self.sql_editor.editor.insert(cursor_pos, sql)
        
        # Highlight the inserted text
        new_end = self.sql_editor.editor.index(f"{cursor_pos}+{len(sql)}c")
        self.highlight_replaced_text(cursor_pos, new_end)
    
    def is_query_complete(self, sql):
        """Check if the SQL query appears to be complete."""
        sql = sql.strip()
        
        # Check basic completeness indicators
        if not sql:
            return False
        
        # Check if it ends with semicolon
        if not sql.endswith(';'):
            return False
        
        # Check for common incomplete patterns
        incomplete_patterns = [
            'SELECT * FROM',  # Missing WHERE clause
            'WHERE',  # Missing condition
            'ORDER BY',  # Missing column
            'GROUP BY',  # Missing column
            'HAVING',  # Missing condition
            'JOIN',  # Missing table
            'ON',  # Missing condition
        ]
        
        for pattern in incomplete_patterns:
            if sql.upper().endswith(pattern.upper()):
                return False
        
        # Check if it has basic SQL structure
        sql_upper = sql.upper()
        if 'SELECT' in sql_upper and 'FROM' in sql_upper:
            return True
        elif any(keyword in sql_upper for keyword in ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']):
            return True
        
        return True  # Default to complete if we can't determine
    
    def highlight_replaced_text(self, start_pos, end_pos):
        """Highlight replaced/inserted text with a special color."""
        try:
            # Configure highlighting tags
            self.sql_editor.editor.tag_configure("ai_replaced", 
                                                background="#2d4a2d",  # Dark green background
                                                foreground="#90EE90",  # Light green text
                                                relief="raised",
                                                borderwidth=1)
            
            # Apply the highlight tag
            self.sql_editor.editor.tag_add("ai_replaced", start_pos, end_pos)
            
            # Auto-remove highlight after 5 seconds
            self.modal_window.after(5000, lambda: self.remove_highlight("ai_replaced"))
            
        except Exception as e:
            print(f"Error highlighting text: {e}")
    
    def highlight_selected_text(self, start_pos, end_pos):
        """Highlight selected text with a different color."""
        try:
            # Configure selection highlighting tags with more visible colors
            self.sql_editor.editor.tag_configure("ai_selected", 
                                                background="#8B0000",  # Dark red background
                                                foreground="#FFFFFF",  # White text for better contrast
                                                relief="raised",
                                                borderwidth=2)
            
            # Apply the highlight tag
            self.sql_editor.editor.tag_add("ai_selected", start_pos, end_pos)
            
            # Auto-remove highlight after 3 seconds
            self.modal_window.after(3000, lambda: self.remove_highlight("ai_selected"))
            
        except Exception as e:
            print(f"Error highlighting selected text: {e}")
    
    def remove_highlight(self, tag_name):
        """Remove highlighting from text."""
        try:
            self.sql_editor.editor.tag_remove(tag_name, "1.0", tk.END)
        except Exception as e:
            print(f"Error removing highlight: {e}")
    
    def remove_all_highlights(self):
        """Remove all AI-related highlights."""
        try:
            self.sql_editor.editor.tag_remove("ai_selected", "1.0", tk.END)
            self.sql_editor.editor.tag_remove("ai_replaced", "1.0", tk.END)
        except Exception as e:
            print(f"Error removing highlights: {e}")
    
    def on_editor_click(self, event):
        """Handle click events in the SQL editor to remove highlights."""
        self.remove_all_highlights()
    
    def on_editor_key(self, event):
        """Handle key events in the SQL editor to remove highlights."""
        self.remove_all_highlights()
    
    def try_alternative_generation(self, prompt, schema, selected_text):
        """Try alternative generation approach for very short queries."""
        self.input_var.set("🔄 Trying alternative approach...")
        self.modal_window.update()
        
        # Try a simpler, more direct prompt
        simple_prompt = f"Write a complete SQL query for: {prompt}\n\nMake sure to include all necessary parts and end with semicolon."
        
        try:
            generated_sql = self.ai_integration.generate_sql_query(simple_prompt, schema)
            if generated_sql and len(generated_sql.strip()) > 50:
                print(f"Alternative generation successful: {repr(generated_sql)}")
                self.add_to_history(prompt, generated_sql)
                self.show_confirmation_prompt(generated_sql, selected_text)
                
                self.input_entry.configure(state="normal")
                self.input_var.set("✅ Generated successfully!")
                self.modal_window.after(2000, lambda: self.input_var.set(""))
            else:
                print(f"Alternative generation also failed: {repr(generated_sql)}")
                self.handle_incomplete_query(generated_sql or "Query generation failed", prompt, selected_text)
        except Exception as e:
            print(f"Alternative generation error: {e}")
            self._show_error(f"❌ Error: {str(e)}")
    
    def handle_incomplete_query(self, partial_sql, original_prompt, selected_text):
        """Handle incomplete query by asking user if they want to continue."""
        from tkinter import messagebox
        
        response = messagebox.askyesno(
            "Query May Be Incomplete",
            f"The generated SQL appears to be incomplete:\n\n{partial_sql[:200]}{'...' if len(partial_sql) > 200 else ''}\n\nDo you want to:\n• Yes: Insert this partial query and continue\n• No: Try generating again",
            icon="warning"
        )
        
        if response:
            # User wants to insert the partial query
            self.add_to_history(original_prompt, partial_sql)
            self.show_confirmation_prompt(partial_sql, selected_text)
            
            # Show success
            self.input_entry.configure(state="normal")
            self.input_var.set("✅ Partial query inserted - you can continue editing")
            self.modal_window.after(3000, lambda: self.input_var.set(""))
        else:
            # User wants to try again
            self.input_entry.configure(state="normal")
            self.input_var.set("🔄 Trying again...")
            self.modal_window.after(1000, self.generate_sql)
    
    def replace_selected_text(self, sql):
        """Replace selected text in the editor with generated SQL."""
        try:
            # Add proper spacing to SQL
            sql = sql.strip()
            if not sql.endswith('\n'):
                sql = sql + '\n'
            
            # Check if there's a selection
            if self.sql_editor.editor.tag_ranges(tk.SEL):
                # Get selection range for highlighting
                sel_start = self.sql_editor.editor.index(tk.SEL_FIRST)
                sel_end = self.sql_editor.editor.index(tk.SEL_LAST)
                
                # Replace the selected text
                self.sql_editor.editor.delete(tk.SEL_FIRST, tk.SEL_LAST)
                insert_pos = self.sql_editor.editor.index(tk.INSERT)
                self.sql_editor.editor.insert(tk.INSERT, sql)
                
                # Calculate new end position after insertion
                new_end = self.sql_editor.editor.index(f"{insert_pos}+{len(sql)}c")
                
                # Highlight the replaced text with a different color
                self.highlight_replaced_text(insert_pos, new_end)
            else:
                # No selection, insert at cursor position
                cursor_pos = self.sql_editor.editor.index(tk.INSERT)
                self.sql_editor.editor.insert(cursor_pos, sql)
                
                # Highlight the inserted text
                new_end = self.sql_editor.editor.index(f"{cursor_pos}+{len(sql)}c")
                self.highlight_replaced_text(cursor_pos, new_end)
        except tk.TclError:
            # Fallback: insert at cursor position
            cursor_pos = self.sql_editor.editor.index(tk.INSERT)
            self.sql_editor.editor.insert(cursor_pos, sql)
            
            # Highlight the inserted text
            new_end = self.sql_editor.editor.index(f"{cursor_pos}+{len(sql)}c")
            self.highlight_replaced_text(cursor_pos, new_end)
        
    def show_sql_popup(self, sql):
        """Show generated SQL in a popup for manual copy."""
        popup = tk.Toplevel(self.modal_window)
        popup.title("Generated SQL")
        popup.geometry("600x400")
        popup.configure(bg="#1e1e1e")
        
        # Make it modal
        popup.transient(self.modal_window)
        popup.grab_set()
        
        # Text area
        text_frame = tk.Frame(popup, bg="#1e1e1e")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, 
                             font=("Consolas", 10),
                             bg="#2d2d2d", fg="#ffffff",
                             relief="flat", bd=1, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert("1.0", sql)
        text_widget.config(state=tk.DISABLED)
        
        # Buttons
        button_frame = tk.Frame(popup, bg="#1e1e1e")
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        copy_btn = tk.Button(button_frame, text="📋 Copy to Editor", 
                           command=lambda: self.copy_to_editor(sql, popup),
                           bg="#007acc", fg="#ffffff", bd=0,
                           font=("Arial", 10))
        copy_btn.pack(side=tk.LEFT, padx=5)
        
        close_btn = tk.Button(button_frame, text="Close", 
                            command=popup.destroy,
                            bg="#6c757d", fg="#ffffff", bd=0,
                            font=("Arial", 10))
        close_btn.pack(side=tk.RIGHT, padx=5)
        
    def copy_to_editor(self, sql, popup):
        """Copy SQL to editor and close popup."""
        # Insert at cursor position instead of replacing entire editor
        self.insert_at_cursor(sql)
        popup.destroy()
        
    def _show_error(self, message):
        """Show error message in the input field."""
        self.input_entry.configure(state="normal")
        self.input_var.set(message)
        self.modal_window.after(3000, lambda: self.input_var.set(""))
        
    def hide_modal(self):
        """Hide the modal and clear history if configured."""
        if not self.is_visible or not self.modal_window:
            return
            
        self.is_visible = False
        
        # Clear conversation history on close
        self.clear_history()
        
        if self.modal_window and self.modal_window.winfo_exists():
            self.modal_window.destroy()
            self.modal_window = None
            
    def _adjust_position(self, x, y):
        """Adjust position to avoid screen edges."""
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        
        # Adjust X position
        if x + self.modal_width > screen_width:
            x = screen_width - self.modal_width - 10
        if x < 10:
            x = 10
            
        # Adjust Y position
        if y + self.modal_height > screen_height:
            y = screen_height - self.modal_height - 10
        if y < 10:
            y = 10
            
        return x, y
        
    def show_at_cursor(self, event):
        """Show modal at cursor position."""
        self.show_modal(event=event)
        
    def show_at_position(self, x, y):
        """Show modal at specific position."""
        self.show_modal(position=(x, y))
        
    def toggle_modal(self, event=None):
        """Toggle modal visibility."""
        if self.is_visible:
            self.hide_modal()
        else:
            self.show_modal(event)
            
    def is_modal_visible(self):
        """Check if modal is currently visible."""
        return self.is_visible and self.modal_window and self.modal_window.winfo_exists()
