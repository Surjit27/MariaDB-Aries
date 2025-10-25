import tkinter as tk
import ttkbootstrap as ttk
from ui.components.modern_theme import ModernTheme

class AIPopup:
    def __init__(self, parent, ai_integration, sql_editor, db_manager):
        self.parent = parent
        self.ai_integration = ai_integration
        self.sql_editor = sql_editor
        self.db_manager = db_manager
        self.theme = ModernTheme()
        self.popup_window = None
        
    def show_popup(self, event):
        """Show AI popup on right-click."""
        if self.popup_window and self.popup_window.winfo_exists():
            self.popup_window.destroy()
        
        # Get cursor position
        x = event.x_root
        y = event.y_root
        
        # Create popup window
        self.popup_window = tk.Toplevel(self.parent)
        self.popup_window.wm_overrideredirect(True)
        self.popup_window.wm_geometry(f"+{x}+{y}")
        self.popup_window.configure(bg="#2d2d2d")
        
        # Create popup frame
        popup_frame = tk.Frame(self.popup_window, bg="#2d2d2d", relief="raised", bd=1)
        popup_frame.pack()
        
        # AI input
        input_frame = tk.Frame(popup_frame, bg="#2d2d2d")
        input_frame.pack(fill=tk.X, padx=8, pady=8)
        
        # AI icon
        ai_icon = tk.Label(input_frame, text="🤖", font=("Arial", 12), bg="#2d2d2d", fg="#ffffff")
        ai_icon.pack(side=tk.LEFT, padx=(0, 5))
        
        # Input entry
        self.input_entry = tk.Entry(input_frame, 
                              font=("Consolas", 10),
                              bg="#404040", fg="#ffffff",
                              insertbackground="#ffffff",
                              relief="flat", bd=1,
                              width=40)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_entry.focus()
        
        # Bind special characters
        self.input_entry.bind("<KeyPress>", self.on_key_press)
        
        # Generate button
        generate_btn = tk.Button(input_frame, text="Generate", 
                               command=self.generate_sql,
                               bg="#007acc", fg="#ffffff", bd=0,
                               font=("Consolas", 9), width=8, height=1,
                               activebackground="#005a9e", activeforeground="#ffffff")
        generate_btn.pack(side=tk.RIGHT)
        
        # Bind Enter key
        self.input_entry.bind("<Return>", lambda e: self.generate_sql())
        
        # Bind escape to close
        self.popup_window.bind("<Escape>", lambda e: self.close_popup())
        self.popup_window.bind("<FocusOut>", lambda e: self.close_popup())
        
        # Auto-focus
        self.input_entry.focus()
    
    def generate_sql(self):
        """Generate SQL using AI."""
        prompt = self.input_entry.get().strip()
        if not prompt:
            return
        
        # Show loading
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, "🤖 Generating...")
        self.input_entry.configure(state="disabled")
        self.popup_window.update()
        
        try:
            # Get current database schema for context
            schema = None
            if self.db_manager and self.db_manager.current_db:
                try:
                    tables = self.db_manager.get_tables()
                    schema = {"tables": tables}
                except:
                    pass
            
            # Generate SQL using AI
            if self.ai_integration:
                generated_sql = self.ai_integration.generate_sql_query(prompt, schema)
                if generated_sql:
                    # Insert generated SQL into editor
                    if self.sql_editor and hasattr(self.sql_editor, 'editor'):
                        self.sql_editor.editor.delete("1.0", tk.END)
                        self.sql_editor.editor.insert("1.0", generated_sql)
                    
                    # Close popup
                    self.close_popup()
                else:
                    self.input_entry.configure(state="normal")
                    self.input_entry.delete(0, tk.END)
                    self.input_entry.insert(0, "❌ Failed to generate SQL")
            else:
                self.input_entry.configure(state="normal")
                self.input_entry.delete(0, tk.END)
                self.input_entry.insert(0, "❌ AI not available")
        except Exception as e:
            self.input_entry.configure(state="normal")
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, f"❌ Error: {str(e)}")
    
    def on_key_press(self, event):
        """Handle key press events for special characters."""
        # Allow @ and # characters
        if event.char in ['@', '#']:
            return  # Let the character be inserted
        # Allow normal characters
        if event.char and event.char.isprintable():
            return  # Let the character be inserted
        # Allow special keys
        if event.keysym in ['BackSpace', 'Delete', 'Left', 'Right', 'Up', 'Down', 'Home', 'End']:
            return  # Let the key work normally
        # Allow Ctrl combinations
        if event.state & 0x4:  # Ctrl key pressed
            return  # Let Ctrl combinations work
    
    def close_popup(self):
        """Close the popup."""
        if self.popup_window and self.popup_window.winfo_exists():
            self.popup_window.destroy()
            self.popup_window = None
