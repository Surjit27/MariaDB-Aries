import tkinter as tk
import ttkbootstrap as ttk
import sys
import os
from typing import Optional, Callable

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ui.components.modern_theme import ModernTheme

class CompactAIModal:
    """
    A compact, tooltip-like AI modal that appears on demand and auto-hides intelligently.
    Designed to be minimal, unobtrusive, and highly functional.
    """
    
    def __init__(self, parent, ai_integration, sql_editor, db_manager):
        self.parent = parent
        self.ai_integration = ai_integration
        self.sql_editor = sql_editor
        self.db_manager = db_manager
        self.theme = ModernTheme()
        
        # Modal state
        self.modal_window = None
        self.input_entry = None
        self.is_visible = False
        self.auto_hide_timer = None
        
        # Configuration
        self.modal_width = 400
        self.modal_height = 50
        self.auto_hide_delay = 5000  # 5 seconds
        self.fade_duration = 200  # 200ms fade
        
    def show_modal(self, event=None, initial_text="", position=None):
        """Show the compact AI modal with smart positioning."""
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
        
        # Create main frame with subtle shadow effect
        main_frame = tk.Frame(self.modal_window, bg="#2d2d2d", relief="raised", bd=1)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Create content frame
        content_frame = tk.Frame(main_frame, bg="#2d2d2d")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        
        # AI icon (compact)
        ai_icon = tk.Label(content_frame, text="🤖", font=("Arial", 10), 
                          bg="#2d2d2d", fg="#ffffff")
        ai_icon.pack(side=tk.LEFT, padx=(0, 6))
        
        # Input entry (compact)
        self.input_entry = tk.Entry(content_frame, 
                                   font=("Consolas", 9),
                                   bg="#404040", fg="#ffffff",
                                   insertbackground="#ffffff",
                                   relief="flat", bd=0,
                                   width=35)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        
        # Action buttons (compact)
        button_frame = tk.Frame(content_frame, bg="#2d2d2d")
        button_frame.pack(side=tk.RIGHT)
        
        # Generate button (compact)
        generate_btn = tk.Button(button_frame, text="▶", 
                               command=self.generate_sql,
                               bg="#007acc", fg="#ffffff", bd=0,
                               font=("Arial", 8, "bold"), 
                               width=2, height=1,
                               activebackground="#005a9e", 
                               activeforeground="#ffffff",
                               relief="flat")
        generate_btn.pack(side=tk.LEFT, padx=(0, 3))
        
        # Close button (compact)
        close_btn = tk.Button(button_frame, text="✕", 
                            command=self.hide_modal,
                            bg="#666666", fg="#ffffff", bd=0,
                            font=("Arial", 8, "bold"), 
                            width=2, height=1,
                            activebackground="#888888", 
                            activeforeground="#ffffff",
                            relief="flat")
        close_btn.pack(side=tk.LEFT)
        
        # Set initial text
        if initial_text:
            self.input_entry.insert(0, initial_text)
        else:
            self.input_entry.insert(0, "Ask AI to generate SQL...")
            
        # Bind events
        self.input_entry.bind("<Return>", lambda e: self.generate_sql())
        self.input_entry.bind("<Escape>", lambda e: self.hide_modal())
        self.input_entry.bind("<FocusIn>", self._on_focus_in)
        self.input_entry.bind("<FocusOut>", self._on_focus_out)
        self.input_entry.bind("<KeyPress>", self._on_key_press)
        
        # Bind modal events
        self.modal_window.bind("<FocusOut>", self._on_modal_focus_out)
        self.modal_window.bind("<Button-1>", self._on_modal_click)
        
        # Focus and select text
        self.input_entry.focus()
        self.input_entry.select_range(0, tk.END)
        
        # Start auto-hide timer
        self._start_auto_hide_timer()
        
    def hide_modal(self):
        """Hide the modal with fade effect."""
        if not self.is_visible or not self.modal_window:
            return
            
        self.is_visible = False
        self._cancel_auto_hide_timer()
        
        if self.modal_window and self.modal_window.winfo_exists():
            # Fade out effect
            self._fade_out()
            
    def _fade_out(self):
        """Fade out the modal window."""
        if not self.modal_window or not self.modal_window.winfo_exists():
            return
            
        try:
            current_alpha = self.modal_window.wm_attributes("-alpha")
            if current_alpha > 0.1:
                new_alpha = max(0.0, current_alpha - 0.1)
                self.modal_window.wm_attributes("-alpha", new_alpha)
                self.modal_window.after(self.fade_duration // 10, self._fade_out)
            else:
                self.modal_window.destroy()
                self.modal_window = None
        except tk.TclError:
            # Window was already destroyed
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
        
    def _start_auto_hide_timer(self):
        """Start the auto-hide timer."""
        self._cancel_auto_hide_timer()
        self.auto_hide_timer = self.modal_window.after(self.auto_hide_delay, self.hide_modal)
        
    def _cancel_auto_hide_timer(self):
        """Cancel the auto-hide timer."""
        if self.auto_hide_timer:
            self.modal_window.after_cancel(self.auto_hide_timer)
            self.auto_hide_timer = None
            
    def _on_focus_in(self, event):
        """Handle focus in event."""
        self._cancel_auto_hide_timer()
        
    def _on_focus_out(self, event):
        """Handle focus out event."""
        # Only start timer if focus didn't move to another widget in the modal
        if self.modal_window and self.modal_window.winfo_exists():
            self._start_auto_hide_timer()
            
    def _on_modal_focus_out(self, event):
        """Handle modal focus out event."""
        # Check if focus moved to parent window
        try:
            focused = self.parent.focus_get()
            if focused and focused != self.input_entry:
                self.hide_modal()
        except tk.TclError:
            pass
            
    def _on_modal_click(self, event):
        """Handle click on modal to prevent auto-hide."""
        self._cancel_auto_hide_timer()
        
    def _on_key_press(self, event):
        """Handle key press events."""
        # Cancel auto-hide on any key press
        self._cancel_auto_hide_timer()
        
        # Allow special characters
        if event.char in ['@', '#', '$']:
            return
        if event.char and event.char.isprintable():
            return
        if event.keysym in ['BackSpace', 'Delete', 'Left', 'Right', 'Up', 'Down', 'Home', 'End']:
            return
        if event.state & 0x4:  # Ctrl key pressed
            return
            
    def generate_sql(self):
        """Generate SQL using AI."""
        prompt = self.input_entry.get().strip()
        if not prompt or prompt == "Ask AI to generate SQL...":
            return
            
        # Show loading state
        self.input_entry.configure(state="disabled")
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, "🤖 Generating...")
        self.modal_window.update()
        
        try:
            # Get database schema for context
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
                    
                    # Show success and hide modal
                    self.input_entry.configure(state="normal")
                    self.input_entry.delete(0, tk.END)
                    self.input_entry.insert(0, "✅ Generated successfully!")
                    self.modal_window.after(1000, self.hide_modal)
                else:
                    self._show_error("❌ Failed to generate SQL")
            else:
                self._show_error("❌ AI not available")
        except Exception as e:
            self._show_error(f"❌ Error: {str(e)}")
            
    def _show_error(self, message):
        """Show error message in the input field."""
        self.input_entry.configure(state="normal")
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, message)
        self.modal_window.after(2000, self.hide_modal)
        
    def show_at_cursor(self, event):
        """Show modal at cursor position."""
        self.show_modal(event=event)
        
    def show_at_position(self, x, y, initial_text=""):
        """Show modal at specific position."""
        self.show_modal(position=(x, y), initial_text=initial_text)
        
    def toggle_modal(self, event=None):
        """Toggle modal visibility."""
        if self.is_visible:
            self.hide_modal()
        else:
            self.show_modal(event)
            
    def is_modal_visible(self):
        """Check if modal is currently visible."""
        return self.is_visible and self.modal_window and self.modal_window.winfo_exists()


class CompactAITooltip:
    """
    An even more compact AI tooltip that appears as a small floating widget.
    """
    
    def __init__(self, parent, ai_integration, sql_editor, db_manager):
        self.parent = parent
        self.ai_integration = ai_integration
        self.sql_editor = sql_editor
        self.db_manager = db_manager
        self.theme = ModernTheme()
        
        # Tooltip state
        self.tooltip_window = None
        self.input_entry = None
        self.is_visible = False
        
    def show_tooltip(self, event=None, position=None):
        """Show the compact AI tooltip."""
        if self.is_visible:
            self.hide_tooltip()
            return
            
        self.is_visible = True
        
        # Calculate position
        if position:
            x, y = position
        elif event:
            x = event.x_root
            y = event.y_root
        else:
            x = self.parent.winfo_rootx() + 50
            y = self.parent.winfo_rooty() + 50
            
        # Create tooltip window
        self.tooltip_window = tk.Toplevel(self.parent)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"300x35+{x}+{y}")
        self.tooltip_window.configure(bg="#2d2d2d")
        self.tooltip_window.wm_attributes("-topmost", True)
        self.tooltip_window.wm_attributes("-alpha", 0.9)
        
        # Create main frame
        main_frame = tk.Frame(self.tooltip_window, bg="#2d2d2d", relief="raised", bd=1)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Create content frame
        content_frame = tk.Frame(main_frame, bg="#2d2d2d")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        
        # AI icon
        ai_icon = tk.Label(content_frame, text="🤖", font=("Arial", 9), 
                          bg="#2d2d2d", fg="#ffffff")
        ai_icon.pack(side=tk.LEFT, padx=(0, 4))
        
        # Input entry
        self.input_entry = tk.Entry(content_frame, 
                                   font=("Consolas", 8),
                                   bg="#404040", fg="#ffffff",
                                   insertbackground="#ffffff",
                                   relief="flat", bd=0,
                                   width=25)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        
        # Generate button
        generate_btn = tk.Button(content_frame, text="▶", 
                               command=self.generate_sql,
                               bg="#007acc", fg="#ffffff", bd=0,
                               font=("Arial", 7, "bold"), 
                               width=1, height=1,
                               activebackground="#005a9e", 
                               activeforeground="#ffffff",
                               relief="flat")
        generate_btn.pack(side=tk.RIGHT)
        
        # Set placeholder text
        self.input_entry.insert(0, "Ask AI...")
        
        # Bind events
        self.input_entry.bind("<Return>", lambda e: self.generate_sql())
        self.input_entry.bind("<Escape>", lambda e: self.hide_tooltip())
        self.input_entry.bind("<FocusIn>", self._on_focus_in)
        
        # Focus and select
        self.input_entry.focus()
        self.input_entry.select_range(0, tk.END)
        
    def hide_tooltip(self):
        """Hide the tooltip."""
        if self.tooltip_window and self.tooltip_window.winfo_exists():
            self.tooltip_window.destroy()
        self.tooltip_window = None
        self.is_visible = False
        
    def _on_focus_in(self, event):
        """Handle focus in event."""
        if self.input_entry.get() == "Ask AI...":
            self.input_entry.delete(0, tk.END)
            
    def generate_sql(self):
        """Generate SQL using AI."""
        prompt = self.input_entry.get().strip()
        if not prompt or prompt == "Ask AI...":
            return
            
        # Show loading
        self.input_entry.configure(state="disabled")
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, "🤖...")
        self.tooltip_window.update()
        
        try:
            # Get schema context
            schema = None
            if self.db_manager and self.db_manager.current_db:
                try:
                    tables = self.db_manager.get_tables()
                    schema = {"tables": tables}
                except:
                    pass
            
            # Generate SQL
            if self.ai_integration:
                generated_sql = self.ai_integration.generate_sql_query(prompt, schema)
                if generated_sql:
                    # Insert into editor
                    if self.sql_editor and hasattr(self.sql_editor, 'editor'):
                        self.sql_editor.editor.delete("1.0", tk.END)
                        self.sql_editor.editor.insert("1.0", generated_sql)
                    
                    # Show success
                    self.input_entry.configure(state="normal")
                    self.input_entry.delete(0, tk.END)
                    self.input_entry.insert(0, "✅ Done!")
                    self.tooltip_window.after(800, self.hide_tooltip)
                else:
                    self._show_error("❌ Failed")
            else:
                self._show_error("❌ No AI")
        except Exception as e:
            self._show_error("❌ Error")
            
    def _show_error(self, message):
        """Show error message."""
        self.input_entry.configure(state="normal")
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, message)
        self.tooltip_window.after(1000, self.hide_tooltip)
