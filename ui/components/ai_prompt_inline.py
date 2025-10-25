import tkinter as tk
import ttkbootstrap as ttk
from typing import List, Dict, Any, Callable, Optional
import re

class InlineAIPrompt:
    def __init__(self, parent, db_manager, ai_integration):
        self.parent = parent
        self.db_manager = db_manager
        self.ai_integration = ai_integration
        self.prompt_frame = None
        self.prompt_entry = None
        self.dropdown = None
        self.dropdown_items = []
        self.current_position = 0
        self.symbol_type = None
        self.is_visible = False
        
    def show_prompt(self, selected_text="", full_query=""):
        """Show the horizontal AI prompt box."""
        if self.is_visible:
            self.hide_prompt()
            return
            
        self.is_visible = True
        
        # Create horizontal prompt frame
        self.prompt_frame = ttk.Frame(self.parent, style="AIPrompt.TFrame")
        self.prompt_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        
        # Configure style
        style = ttk.Style()
        style.configure("AIPrompt.TFrame", background="#e3f2fd", relief="raised", borderwidth=1)
        
        # Create prompt container
        container = ttk.Frame(self.prompt_frame)
        container.pack(fill=tk.X, padx=5, pady=5)
        
        # AI label
        ai_label = ttk.Label(container, text="🤖 AI:", font=("Arial", 9, "bold"))
        ai_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Prompt entry
        self.prompt_entry = tk.Text(container, height=2, wrap=tk.WORD, font=("Arial", 10))
        self.prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Pre-fill with context if provided
        if selected_text:
            self.prompt_entry.insert("1.0", f"Optimize this query: {selected_text}")
        elif full_query:
            self.prompt_entry.insert("1.0", f"Generate SQL for: {full_query}")
        else:
            self.prompt_entry.insert("1.0", "Type your request in English...")
        
        # Bind events for autocomplete
        self.prompt_entry.bind("<KeyRelease>", self.on_key_release)
        self.prompt_entry.bind("<Button-1>", self.on_click)
        self.prompt_entry.bind("<FocusOut>", self.hide_dropdown)
        
        # Buttons
        button_frame = ttk.Frame(container)
        button_frame.pack(side=tk.RIGHT)
        
        ttk.Button(button_frame, text="Generate", command=self.generate_sql, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Optimize", command=self.optimize_query, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Close", command=self.hide_prompt, width=6).pack(side=tk.LEFT, padx=2)
        
        # Focus on entry
        self.prompt_entry.focus_set()
        self.prompt_entry.tag_add(tk.SEL, "1.0", tk.END)
        
    def hide_prompt(self):
        """Hide the AI prompt box."""
        if self.prompt_frame:
            self.prompt_frame.destroy()
            self.prompt_frame = None
        self.is_visible = False
        
    def on_key_release(self, event):
        """Handle key release for autocomplete."""
        if event.keysym in ['Up', 'Down', 'Return']:
            return self.handle_dropdown_navigation(event)
            
        try:
            # Get current cursor position and text
            cursor_pos = self.prompt_entry.index(tk.INSERT)
            text = self.prompt_entry.get("1.0", tk.END)
            
            # Convert cursor position to integer
            try:
                if '.' in cursor_pos:
                    line, col = cursor_pos.split('.')
                    cursor_pos_int = int(col)
                else:
                    cursor_pos_int = 0
            except (ValueError, IndexError):
                cursor_pos_int = 0
            
            # Check for @ or $ symbols
            line_start = text.rfind('\n', 0, cursor_pos_int)
            if line_start == -1:
                line_start = 0
            else:
                line_start += 1
                
            current_line = text[line_start:cursor_pos_int]
            
            # Check for @ symbol (databases/tables)
            at_match = re.search(r'@(\w*)$', current_line)
            if at_match:
                self.show_dropdown('@', at_match.start() + line_start, at_match.end() + line_start)
                return
                
            # Check for $ symbol (selected tables)
            dollar_match = re.search(r'\$(\w*)$', current_line)
            if dollar_match:
                self.show_dropdown('$', dollar_match.start() + line_start, dollar_match.end() + line_start)
                return
                
            # Hide dropdown if no symbols
            self.hide_dropdown()
            
        except Exception as e:
            print(f"Error in on_key_release: {e}")
            self.hide_dropdown()
        
    def on_click(self, event):
        """Handle click to hide dropdown."""
        self.hide_dropdown()
        
    def show_dropdown(self, symbol_type, start_pos, end_pos):
        """Show autocomplete dropdown."""
        self.symbol_type = symbol_type
        self.current_position = end_pos
        
        # Hide existing dropdown
        self.hide_dropdown()
        
        # Get items based on symbol type
        if symbol_type == '@':
            items = self.get_database_items()
        else:  # $
            items = self.get_selected_table_items()
            
        if not items:
            return
            
        # Create dropdown
        self.dropdown = tk.Toplevel(self.parent)
        self.dropdown.wm_overrideredirect(True)
        self.dropdown.wm_attributes("-topmost", True)
        
        # Position dropdown
        try:
            bbox = self.prompt_entry.bbox(tk.INSERT)
            if bbox:
                x = self.parent.winfo_rootx() + self.prompt_entry.winfo_x() + bbox[0]
                y = self.parent.winfo_rooty() + self.prompt_entry.winfo_y() + bbox[1] + bbox[3]
            else:
                x = self.parent.winfo_rootx() + 50
                y = self.parent.winfo_rooty() + 100
        except tk.TclError:
            x = self.parent.winfo_rootx() + 50
            y = self.parent.winfo_rooty() + 100
            
        self.dropdown.geometry(f"250x150+{x}+{y}")
        
        # Create listbox
        listbox_frame = ttk.Frame(self.dropdown)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        self.dropdown_listbox = tk.Listbox(listbox_frame, font=("Arial", 9))
        self.dropdown_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Add items
        self.dropdown_items = items
        for item in items:
            self.dropdown_listbox.insert(tk.END, item)
            
        # Bind selection
        self.dropdown_listbox.bind("<Double-Button-1>", self.select_item)
        self.dropdown_listbox.bind("<Return>", self.select_item)
        self.dropdown_listbox.bind("<Escape>", lambda e: self.hide_dropdown())
        
        # Select first item
        if items:
            self.dropdown_listbox.selection_set(0)
            
    def hide_dropdown(self, event=None):
        """Hide the dropdown."""
        if self.dropdown:
            self.dropdown.destroy()
            self.dropdown = None
            
    def get_database_items(self):
        """Get database and table items for @ symbol."""
        items = []
        
        # Add databases
        try:
            databases = self.db_manager.get_databases()
            for db in databases:
                items.append(f"database:{db}")
        except Exception as e:
            print(f"Error getting databases: {e}")
            
        # Add tables from current database
        if self.db_manager.current_db:
            try:
                tables = self.db_manager.get_tables()
                for table in tables:
                    items.append(f"table:{table}")
            except Exception as e:
                print(f"Error getting tables: {e}")
                
        return items
        
    def get_selected_table_items(self):
        """Get selected table items for $ symbol."""
        if self.db_manager.current_db:
            try:
                tables = self.db_manager.get_tables()
                return [f"table:{table}" for table in tables]
            except Exception as e:
                print(f"Error getting selected tables: {e}")
                return []
        return []
        
    def select_item(self, event=None):
        """Select an item from dropdown."""
        selection = self.dropdown_listbox.curselection()
        if selection:
            item = self.dropdown_items[selection[0]]
            self.insert_autocomplete(item)
        self.hide_dropdown()
        
    def insert_autocomplete(self, item):
        """Insert the selected item into the text."""
        try:
            # Get the text before the symbol
            cursor_pos = self.prompt_entry.index(tk.INSERT)
            text = self.prompt_entry.get("1.0", cursor_pos)
            
            # Find the last @ or $ symbol
            at_pos = text.rfind('@')
            dollar_pos = text.rfind('$')
            
            if at_pos > dollar_pos:
                # Replace from @ symbol
                new_text = text[:at_pos] + f"@{item}" + " "
                self.prompt_entry.delete("1.0", cursor_pos)
                self.prompt_entry.insert("1.0", new_text)
                self.prompt_entry.mark_set(tk.INSERT, f"1.{len(new_text)}")
            elif dollar_pos > at_pos:
                # Replace from $ symbol
                new_text = text[:dollar_pos] + f"${item}" + " "
                self.prompt_entry.delete("1.0", cursor_pos)
                self.prompt_entry.insert("1.0", new_text)
                self.prompt_entry.mark_set(tk.INSERT, f"1.{len(new_text)}")
        except Exception as e:
            print(f"Error inserting autocomplete: {e}")
            
    def handle_dropdown_navigation(self, event):
        """Handle navigation in dropdown."""
        if not self.dropdown or not self.dropdown_listbox:
            return
            
        if event.keysym == 'Up':
            current = self.dropdown_listbox.curselection()
            if current and current[0] > 0:
                self.dropdown_listbox.selection_clear(current[0])
                self.dropdown_listbox.selection_set(current[0] - 1)
            return "break"
        elif event.keysym == 'Down':
            current = self.dropdown_listbox.curselection()
            if current and current[0] < len(self.dropdown_items) - 1:
                self.dropdown_listbox.selection_clear(current[0])
                self.dropdown_listbox.selection_set(current[0] + 1)
            return "break"
        elif event.keysym == 'Return':
            self.select_item()
            return "break"
            
    def generate_sql(self):
        """Generate SQL from the prompt using RAG mechanism."""
        prompt = self.prompt_entry.get("1.0", tk.END).strip()
        if not prompt:
            return
            
        # Get database schema context
        schema_context = self.get_database_schema()
        
        # Create RAG prompt with structured format
        rag_prompt = self.create_rag_prompt(prompt, schema_context)
        
        if self.ai_integration:
            # Generate SQL using AI with RAG
            generated_sql = self.ai_integration.generate_sql_query(rag_prompt)
            if generated_sql:
                # Insert the generated SQL into the main editor
                self.insert_sql_to_editor(generated_sql)
                self.hide_prompt()
            else:
                self.show_error("Failed to generate SQL with AI.")
        else:
            self.show_error("AI integration not available. API key may not be set.")
            
    def optimize_query(self):
        """Optimize the selected query using RAG mechanism."""
        # Get the selected text from the main editor
        selected_text = self.get_selected_text()
        if not selected_text:
            self.show_error("No query selected to optimize.")
            return
            
        # Get database schema context
        schema_context = self.get_database_schema()
        
        # Create optimization prompt
        optimization_prompt = self.create_optimization_prompt(selected_text, schema_context)
        
        if self.ai_integration:
            # Optimize query using AI
            optimized_sql = self.ai_integration.generate_sql_query(optimization_prompt)
            if optimized_sql:
                # Replace the selected text with optimized version
                self.replace_selected_text(optimized_sql)
                self.hide_prompt()
            else:
                self.show_error("Failed to optimize query with AI.")
        else:
            self.show_error("AI integration not available. API key may not be set.")
            
    def create_rag_prompt(self, user_prompt, schema_context):
        """Create a structured RAG prompt for SQL generation."""
        return f"""Database Schema Context:
{schema_context}

User Request: {user_prompt}

Generate SQL Query:
- Return ONLY the SQL command
- Use proper SQL syntax
- Include appropriate WHERE clauses
- Use JOINs when needed
- Format the query properly

SQL Query:"""
        
    def create_optimization_prompt(self, selected_query, schema_context):
        """Create a structured prompt for query optimization."""
        return f"""Database Schema Context:
{schema_context}

Selected Query to Optimize:
{selected_query}

Optimize this SQL query:
- Return ONLY the optimized SQL command
- Improve performance with proper indexing hints
- Use efficient JOINs and WHERE clauses
- Add appropriate comments for optimization reasons
- Maintain the same functionality

Optimized SQL Query:"""
        
    def get_database_schema(self):
        """Get the current database schema for the prompt."""
        if not self.db_manager.current_db:
            return "No database currently open."
        
        schema_info = f"Database: {self.db_manager.current_db}\n"
        
        try:
            # Get tables
            tables = self.db_manager.get_tables()
            if tables:
                schema_info += f"Tables: {', '.join(tables)}\n"
                
                # Get columns for each table
                for table in tables:
                    try:
                        columns = self.db_manager.get_columns(table)
                        if columns:
                            column_info = ', '.join([f"{col['name']} ({col['type']})" for col in columns])
                            schema_info += f"  {table}: {column_info}\n"
                    except Exception as e:
                        schema_info += f"  {table}: Error getting columns - {str(e)}\n"
            else:
                schema_info += "No tables found in the database.\n"
                
        except Exception as e:
            schema_info += f"Error getting schema: {str(e)}\n"
        
        return schema_info
        
    def get_selected_text(self):
        """Get selected text from the main SQL editor."""
        try:
            if hasattr(self.parent, 'sql_editor') and hasattr(self.parent.sql_editor, 'editor'):
                return self.parent.sql_editor.editor.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass
        return ""
        
    def insert_sql_to_editor(self, sql_query):
        """Insert generated SQL into the main editor."""
        try:
            if hasattr(self.parent, 'sql_editor') and hasattr(self.parent.sql_editor, 'editor'):
                self.parent.sql_editor.editor.delete("1.0", tk.END)
                self.parent.sql_editor.editor.insert("1.0", sql_query)
        except Exception as e:
            print(f"Error inserting SQL: {e}")
            
    def replace_selected_text(self, new_sql):
        """Replace selected text with optimized SQL."""
        try:
            if hasattr(self.parent, 'sql_editor') and hasattr(self.parent.sql_editor, 'editor'):
                self.parent.sql_editor.editor.delete(tk.SEL_FIRST, tk.SEL_LAST)
                self.parent.sql_editor.editor.insert(tk.INSERT, new_sql)
        except Exception as e:
            print(f"Error replacing text: {e}")
            
    def show_error(self, message):
        """Show error message."""
        from tkinter import messagebox
        messagebox.showerror("AI Error", message)


class AIContextMenu:
    def __init__(self, parent, db_manager, ai_integration):
        self.parent = parent
        self.db_manager = db_manager
        self.ai_integration = ai_integration
        self.inline_prompt = None
        
    def show_context_menu(self, event):
        """Show the context menu."""
        context_menu = tk.Menu(self.parent, tearoff=0)
        
        # AI options
        context_menu.add_command(label="🤖 AI Generate SQL", command=self.show_ai_generate)
        context_menu.add_command(label="⚡ AI Optimize Query", command=self.show_ai_optimize)
        context_menu.add_separator()
        
        # SQL options
        context_menu.add_command(label="📝 Select All", command=self.select_all)
        context_menu.add_command(label="📋 Copy", command=self.copy_text)
        context_menu.add_command(label="📄 Paste", command=self.paste_text)
        context_menu.add_separator()
        
        # Execute options
        context_menu.add_command(label="▶️ Execute Function", command=self.execute_function)
        context_menu.add_command(label="🔧 Create Trigger", command=self.create_trigger)
        context_menu.add_command(label="👁️ Create View", command=self.create_view)
        context_menu.add_separator()
        
        # Format options
        context_menu.add_command(label="🎨 Format SQL", command=self.format_sql)
        context_menu.add_command(label="🔍 Find & Replace", command=self.find_replace)
        
        # Show context menu
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
            
    def show_ai_generate(self):
        """Show AI generate prompt."""
        if not self.inline_prompt:
            self.inline_prompt = InlineAIPrompt(self.parent, self.db_manager, self.ai_integration)
        self.inline_prompt.show_prompt()
        
    def show_ai_optimize(self):
        """Show AI optimize prompt with selected text."""
        if not self.inline_prompt:
            self.inline_prompt = InlineAIPrompt(self.parent, self.db_manager, self.ai_integration)
        
        # Get selected text
        selected_text = self.get_selected_text()
        self.inline_prompt.show_prompt(selected_text=selected_text)
        
    def get_selected_text(self):
        """Get selected text from editor."""
        try:
            if hasattr(self.parent, 'editor'):
                return self.parent.editor.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass
        return ""
        
    def select_all(self):
        """Select all text."""
        if hasattr(self.parent, 'editor'):
            self.parent.editor.tag_add(tk.SEL, "1.0", tk.END)
            
    def copy_text(self):
        """Copy selected text."""
        if hasattr(self.parent, 'editor'):
            try:
                text = self.parent.editor.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.parent.clipboard_clear()
                self.parent.clipboard_append(text)
            except tk.TclError:
                pass
                
    def paste_text(self):
        """Paste text."""
        if hasattr(self.parent, 'editor'):
            try:
                text = self.parent.clipboard_get()
                self.parent.editor.insert(tk.INSERT, text)
            except tk.TclError:
                pass
                
    def execute_function(self):
        """Execute a function."""
        from tkinter import simpledialog
        function_name = simpledialog.askstring("Execute Function", "Enter function name:")
        if function_name:
            if hasattr(self.parent, 'editor'):
                self.parent.editor.insert(tk.INSERT, f"SELECT {function_name}();")
                
    def create_trigger(self):
        """Create a trigger template."""
        if hasattr(self.parent, 'editor'):
            trigger_template = """
CREATE TRIGGER trigger_name
AFTER INSERT ON table_name
BEGIN
    -- Trigger logic here
END;
"""
            self.parent.editor.insert(tk.INSERT, trigger_template)
            
    def create_view(self):
        """Create a view template."""
        if hasattr(self.parent, 'editor'):
            view_template = """
CREATE VIEW view_name AS
SELECT * FROM table_name
WHERE condition;
"""
            self.parent.editor.insert(tk.INSERT, view_template)
            
    def format_sql(self):
        """Format SQL code."""
        if hasattr(self.parent, 'editor'):
            text = self.parent.editor.get("1.0", tk.END)
            keywords = ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
            for keyword in keywords:
                text = re.sub(rf'\b{keyword.lower()}\b', keyword, text, flags=re.IGNORECASE)
            self.parent.editor.delete("1.0", tk.END)
            self.parent.editor.insert("1.0", text)
            
    def find_replace(self):
        """Open find and replace dialog."""
        from tkinter import simpledialog
        find_text = simpledialog.askstring("Find", "Enter text to find:")
        if find_text:
            replace_text = simpledialog.askstring("Replace", "Enter replacement text:")
            if replace_text and hasattr(self.parent, 'editor'):
                content = self.parent.editor.get("1.0", tk.END)
                new_content = content.replace(find_text, replace_text)
                self.parent.editor.delete("1.0", tk.END)
                self.parent.editor.insert("1.0", new_content)
