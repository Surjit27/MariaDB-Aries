import tkinter as tk
import ttkbootstrap as ttk
from ui.components.modern_theme import ModernTheme
import re

class AIAssistant:
    def __init__(self, parent, ai_integration, sql_editor=None):
        self.parent = parent
        self.ai_integration = ai_integration
        self.sql_editor = sql_editor
        self.theme = ModernTheme()
        self.icons = self.theme.get_emoji_icons()
        self.is_visible = False
        self.suggestions_window = None
        self.create_widgets()
        
    def create_widgets(self):
        """Create the AI assistant interface."""
        # Main AI assistant frame
        self.ai_frame = ttk.Frame(self.parent, style="AIPrompt.TFrame")
        # DISABLED: This AI assistant is deprecated - use HorizontalAIModal instead
        # self.ai_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # AI input bar (disabled)
        # self.create_input_bar()
        
        # Hide the AI assistant by default (deprecated)
        self.ai_frame.pack_forget()  # Always hide - use HorizontalAIModal instead
        
    def create_input_bar(self):
        """Create the horizontal AI input bar."""
        # Input frame
        input_frame = ttk.Frame(self.ai_frame, style="AIPrompt.TFrame")
        input_frame.pack(fill=tk.X, padx=8, pady=8)
        
        # AI icon
        ai_icon = ttk.Label(input_frame, text="🤖", font=("Arial", 14))
        ai_icon.pack(side=tk.LEFT, padx=(0, 8))
        
        # Input entry with placeholder
        self.input_entry = tk.Entry(input_frame, 
                                   font=("Consolas", 11),
                                   bg="#2d2d2d", fg="#ffffff",
                                   insertbackground="#ffffff",
                                   relief="flat", bd=1,
                                   width=60)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        # Placeholder text
        self.placeholder_text = "Ask AI to generate SQL... (e.g., 'Show me all users from New York')"
        self.input_entry.insert(0, self.placeholder_text)
        self.input_entry.configure(fg="#888888")
        
        # Bind events
        self.input_entry.bind("<FocusIn>", self.on_focus_in)
        self.input_entry.bind("<FocusOut>", self.on_focus_out)
        self.input_entry.bind("<KeyRelease>", self.on_key_release)
        self.input_entry.bind("<Return>", self.on_enter_pressed)
        self.input_entry.bind("<KeyPress>", self.on_key_press)
        
        # Action buttons
        self.create_action_buttons(input_frame)
        
    def create_action_buttons(self, parent):
        """Create action buttons for the AI assistant."""
        button_frame = ttk.Frame(parent, style="AIPrompt.TFrame")
        button_frame.pack(side=tk.RIGHT, padx=(8, 0))
        
        # Generate button
        self.generate_btn = tk.Button(button_frame, text="Generate", 
                                    command=self.generate_sql,
                                    bg="#404040", fg="#ffffff", bd=0,
                                    font=("Consolas", 10), width=8, height=1,
                                    activebackground="#555555", activeforeground="#ffffff")
        self.generate_btn.pack(side=tk.LEFT, padx=2)
        
        # Clear button
        self.clear_btn = tk.Button(button_frame, text="Clear", 
                                 command=self.clear_input,
                                 bg="#404040", fg="#ffffff", bd=0,
                                 font=("Consolas", 10), width=6, height=1,
                                 activebackground="#555555", activeforeground="#ffffff")
        self.clear_btn.pack(side=tk.LEFT, padx=2)
        
        # Toggle button
        self.toggle_btn = tk.Button(button_frame, text="Hide", 
                                  command=self.toggle_visibility,
                                  bg="#2d2d2d", fg="#ffffff", bd=0,
                                  font=("Consolas", 10), width=6, height=1,
                                  activebackground="#404040", activeforeground="#ffffff")
        self.toggle_btn.pack(side=tk.LEFT, padx=2)
    
    def on_focus_in(self, event):
        """Handle focus in event."""
        if self.input_entry.get() == self.placeholder_text:
            self.input_entry.delete(0, tk.END)
            self.input_entry.configure(fg="#ffffff")
    
    def on_focus_out(self, event):
        """Handle focus out event."""
        if not self.input_entry.get():
            self.input_entry.insert(0, self.placeholder_text)
            self.input_entry.configure(fg="#888888")
    
    def on_key_release(self, event):
        """Handle key release event for suggestions."""
        current_text = self.input_entry.get()
        if current_text and current_text != self.placeholder_text:
            # Check for @ and $ triggers
            if current_text.endswith('@') or current_text.endswith('$'):
                self.show_suggestions(current_text)
            elif current_text.endswith(' ') and ('@' in current_text or '$' in current_text):
                self.show_suggestions(current_text)
            else:
                self.hide_suggestions()
        else:
            self.hide_suggestions()
    
    def on_key_press(self, event):
        """Handle key press event."""
        # Handle Escape key to hide suggestions
        if event.keysym == "Escape":
            self.hide_suggestions()
        # Handle Tab key to accept suggestion
        elif event.keysym == "Tab":
            if self.suggestions_window and self.suggestions_window.winfo_exists():
                self.accept_suggestion()
                return "break"
    
    def on_enter_pressed(self, event):
        """Handle Enter key press."""
        self.generate_sql()
        return "break"
    
    def show_suggestions(self, text):
        """Show AI suggestions based on input."""
        if not self.ai_integration:
            return
        
        # Extract context for suggestions
        context = ""
        if '@' in text:
            # Database/table suggestions
            context = "database tables"
        elif '$' in text:
            # Column suggestions
            context = "table columns"
        
        # Get suggestions from AI
        suggestions = self.ai_integration.get_suggestions(text, context)
        
        if suggestions:
            self.create_suggestions_window(suggestions)
    
    def create_suggestions_window(self, suggestions):
        """Create suggestions popup window."""
        if self.suggestions_window and self.suggestions_window.winfo_exists():
            self.suggestions_window.destroy()
        
        # Get input entry position
        x = self.input_entry.winfo_rootx()
        y = self.input_entry.winfo_rooty() + self.input_entry.winfo_height()
        
        # Create suggestions window
        self.suggestions_window = tk.Toplevel(self.parent)
        self.suggestions_window.wm_overrideredirect(True)
        self.suggestions_window.wm_geometry(f"+{x}+{y}")
        self.suggestions_window.configure(bg="#2d2d2d")
        
        # Create suggestions list
        suggestions_frame = tk.Frame(self.suggestions_window, bg="#2d2d2d", relief="raised", bd=1)
        suggestions_frame.pack()
        
        self.suggestion_buttons = []
        for i, suggestion in enumerate(suggestions[:5]):  # Limit to 5 suggestions
            btn = tk.Button(suggestions_frame, text=suggestion,
                           bg="#2d2d2d", fg="#ffffff", bd=0,
                           font=("Consolas", 10), anchor="w",
                           activebackground="#404040", activeforeground="#ffffff",
                           command=lambda s=suggestion: self.insert_suggestion(s))
            btn.pack(fill=tk.X, padx=2, pady=1)
            self.suggestion_buttons.append(btn)
        
        # Bind mouse events
        self.suggestions_window.bind("<FocusOut>", lambda e: self.hide_suggestions())
        self.suggestions_window.bind("<Escape>", lambda e: self.hide_suggestions())
    
    def hide_suggestions(self):
        """Hide suggestions window."""
        if self.suggestions_window and self.suggestions_window.winfo_exists():
            self.suggestions_window.destroy()
            self.suggestions_window = None
    
    def accept_suggestion(self):
        """Accept the first suggestion."""
        if self.suggestion_buttons:
            first_btn = self.suggestion_buttons[0]
            suggestion = first_btn.cget("text")
            self.insert_suggestion(suggestion)
    
    def insert_suggestion(self, suggestion):
        """Insert suggestion into input field."""
        current_text = self.input_entry.get()
        
        # Find the last @ or $ and replace with suggestion
        if '@' in current_text:
            last_at = current_text.rfind('@')
            new_text = current_text[:last_at] + suggestion + current_text[last_at + 1:]
        elif '$' in current_text:
            last_dollar = current_text.rfind('$')
            new_text = current_text[:last_dollar] + suggestion + current_text[last_dollar + 1:]
        else:
            new_text = current_text + " " + suggestion
        
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, new_text)
        self.input_entry.configure(fg="#ffffff")
        
        self.hide_suggestions()
    
    def generate_sql(self):
        """Generate SQL using AI."""
        prompt = self.input_entry.get()
        if not prompt or prompt == self.placeholder_text:
            self.show_status("❌ Please enter a prompt first.")
            return
        
        # Show loading message
        self.show_status("🤖 Generating SQL with AI...")
        
        # Get current database schema for context
        schema = None
        if hasattr(self, 'db_manager') and self.db_manager and self.db_manager.current_db:
            try:
                tables = self.db_manager.get_tables()
                schema = {"tables": tables}
            except:
                pass
        
        # Generate SQL using AI
        if self.ai_integration:
            try:
                generated_sql = self.ai_integration.generate_sql_query(prompt, schema)
                if generated_sql:
                    # Insert generated SQL into editor
                    if self.sql_editor and hasattr(self.sql_editor, 'editor'):
                        self.sql_editor.editor.delete("1.0", tk.END)
                        self.sql_editor.editor.insert("1.0", generated_sql)
                    
                    # Clear input
                    self.clear_input()
                    
                    # Show success message
                    self.show_status("✅ SQL generated successfully!")
                else:
                    self.show_status("❌ Failed to generate SQL. Please try again.")
            except Exception as e:
                self.show_status(f"❌ Error: {str(e)}")
        else:
            self.show_status("❌ AI integration not available.")
    
    def clear_input(self):
        """Clear the input field."""
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, self.placeholder_text)
        self.input_entry.configure(fg="#888888")
        self.hide_suggestions()
    
    def toggle_visibility(self):
        """Toggle AI assistant visibility."""
        if self.is_visible:
            self.ai_frame.pack_forget()
            self.toggle_btn.configure(text="Show")
            self.is_visible = False
        else:
            self.ai_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
            self.toggle_btn.configure(text="Hide")
            self.is_visible = True
    
    def show_status(self, message):
        """Show status message."""
        # Create temporary status label
        status_label = ttk.Label(self.ai_frame, text=message, 
                               style="Info.TLabel", font=("Consolas", 9))
        status_label.pack(pady=2)
        
        # Remove after 3 seconds
        self.ai_frame.after(3000, lambda: status_label.destroy())
    
    def set_sql_editor(self, sql_editor):
        """Set reference to SQL editor."""
        self.sql_editor = sql_editor
    
    def set_db_manager(self, db_manager):
        """Set reference to database manager."""
        self.db_manager = db_manager
