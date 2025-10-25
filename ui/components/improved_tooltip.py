import tkinter as tk

class ImprovedTooltip:
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.after_id = None
        
        # Bind events
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<Motion>", self.on_motion)
    
    def on_enter(self, event):
        """Handle mouse enter event."""
        self.schedule_tooltip()
    
    def on_leave(self, event):
        """Handle mouse leave event."""
        self.cancel_tooltip()
        self.hide_tooltip()
    
    def on_motion(self, event):
        """Handle mouse motion event."""
        self.cancel_tooltip()
        self.schedule_tooltip()
    
    def schedule_tooltip(self):
        """Schedule tooltip to appear after delay."""
        self.after_id = self.widget.after(self.delay, self.show_tooltip)
    
    def cancel_tooltip(self):
        """Cancel scheduled tooltip."""
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
    
    def show_tooltip(self):
        """Show the tooltip."""
        if self.tooltip_window:
            return
        
        # Get widget position
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # Create tooltip window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        self.tooltip_window.configure(bg="#2d2d2d")
        
        # Create tooltip label
        label = tk.Label(self.tooltip_window, text=self.text,
                        bg="#2d2d2d", fg="#ffffff",
                        font=("Consolas", 9), relief="raised", bd=1,
                        padx=8, pady=4)
        label.pack()
        
        # Auto-hide after 3 seconds
        self.tooltip_window.after(3000, self.hide_tooltip)
    
    def hide_tooltip(self):
        """Hide the tooltip."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

def create_improved_tooltip(widget, text, delay=500):
    """Create an improved tooltip for a widget."""
    return ImprovedTooltip(widget, text, delay)
