import tkinter as tk
import ttkbootstrap as ttk
from typing import Callable

class SimpleAIPrompt:
    def __init__(self, parent, db_manager, ai_integration):
        self.parent = parent
        self.db_manager = db_manager
        self.ai_integration = ai_integration
        self.prompt_frame = None
        self.is_visible = False
        
    def show_prompt(self, selected_text="", full_query=""):
        """Show a simple horizontal AI prompt box."""
        if self.is_visible:
            self.hide_prompt()
            return
            
        self.is_visible = True
        
        # Create horizontal prompt frame
        self.prompt_frame = ttk.Frame(self.parent, style="AIPrompt.TFrame")
        self.prompt_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        
        # Configure style
        style = ttk.Style()
        style.configure("AIPrompt.TFrame", background="#2d2d2d", relief="raised", borderwidth=1)
        
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
        
    def generate_sql(self):
        """Generate SQL from the prompt."""
        prompt = self.prompt_entry.get("1.0", tk.END).strip()
        if not prompt:
            return
            
        if self.ai_integration:
            # Generate SQL using AI
            generated_sql = self.ai_integration.generate_sql_query(prompt)
            if generated_sql:
                # Insert the generated SQL into the main editor
                self.insert_sql_to_editor(generated_sql)
                self.hide_prompt()
            else:
                self.show_error("Failed to generate SQL with AI.")
        else:
            self.show_error("AI integration not available. API key may not be set.")
            
    def optimize_query(self):
        """Optimize the selected query."""
        # Get the selected text from the main editor
        selected_text = self.get_selected_text()
        if not selected_text:
            self.show_error("No query selected to optimize.")
            return
            
        if self.ai_integration:
            # Optimize query using AI
            optimized_sql = self.ai_integration.generate_sql_query(f"Optimize this SQL query: {selected_text}")
            if optimized_sql:
                # Replace the selected text with optimized version
                self.replace_selected_text(optimized_sql)
                self.hide_prompt()
            else:
                self.show_error("Failed to optimize query with AI.")
        else:
            self.show_error("AI integration not available. API key may not be set.")
            
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
