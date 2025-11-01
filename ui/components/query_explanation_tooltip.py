"""
Query Explanation Tooltip
Shows SQL query explanations in a popup tooltip
"""

import tkinter as tk
from tkinter import ttk
import threading
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai.query_explainer import QueryExplainer

class QueryExplanationTooltip:
    """Popup tooltip for displaying SQL query explanations."""
    
    def __init__(self, parent_widget, db_manager=None):
        """
        Initialize the explanation tooltip.
        
        Args:
            parent_widget: The widget to attach the tooltip to (usually the SQL editor or button)
            db_manager: Optional database manager for schema context
        """
        self.parent_widget = parent_widget
        self.db_manager = db_manager
        self.tooltip_window = None
        self.explainer = None
        
        # Initialize explainer
        api_key = os.getenv('GEMINI_API_KEY', '')
        if api_key:
            self.explainer = QueryExplainer(api_key)
    
    def show_explanation(self, sql_query: str, x: int = None, y: int = None):
        """
        Show explanation tooltip for a SQL query.
        
        Args:
            sql_query: The SQL query to explain
            x, y: Optional screen coordinates (if None, uses mouse position)
        """
        if not sql_query or not sql_query.strip():
            return
        
        # Close existing tooltip if open
        self.hide_tooltip()
        
        # Get position
        if x is None or y is None:
            x = self.parent_widget.winfo_pointerx()
            y = self.parent_widget.winfo_pointery() + 20
        
        # Show loading tooltip first
        self._show_loading_tooltip(x, y)
        
        # Generate explanation in background thread
        thread = threading.Thread(
            target=self._generate_and_show_explanation,
            args=(sql_query, x, y),
            daemon=True
        )
        thread.start()
    
    def _show_loading_tooltip(self, x: int, y: int):
        """Show loading tooltip while generating explanation."""
        self.tooltip_window = tk.Toplevel(self.parent_widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"300x80+{x}+{y}")
        self.tooltip_window.configure(bg="#f8f9fa", relief="solid", bd=1)
        
        # Loading frame
        loading_frame = tk.Frame(self.tooltip_window, bg="#f8f9fa", padx=10, pady=10)
        loading_frame.pack(fill=tk.BOTH, expand=True)
        
        loading_label = tk.Label(
            loading_frame,
            text="⏳ Analyzing query...",
            font=("Arial", 10),
            bg="#f8f9fa",
            fg="#333333"
        )
        loading_label.pack()
        
        self.tooltip_window.update()
    
    def _generate_and_show_explanation(self, sql_query: str, x: int, y: int):
        """Generate explanation and show in tooltip."""
        try:
            # Get schema context if available
            schema = None
            if self.db_manager and hasattr(self.db_manager, 'get_database_schema_for_ai'):
                try:
                    schema = self.db_manager.get_database_schema_for_ai()
                except Exception:
                    pass
            
            # Generate explanation
            if self.explainer and self.explainer.is_api_available():
                explanation = self.explainer.explain_query(sql_query, schema)
            else:
                explanation = "Query explainer not available. Please configure your API key in Settings."
            
            # Update UI in main thread
            self.parent_widget.after(0, lambda: self._show_explanation_tooltip(explanation, x, y))
            
        except Exception as e:
            error_msg = f"Error generating explanation: {str(e)}"
            self.parent_widget.after(0, lambda: self._show_explanation_tooltip(error_msg, x, y))
    
    def _show_explanation_tooltip(self, explanation: str, x: int, y: int):
        """Show the explanation in a tooltip window."""
        # Close loading tooltip
        if self.tooltip_window:
            try:
                self.tooltip_window.destroy()
            except:
                pass
        
        # Create explanation tooltip
        self.tooltip_window = tk.Toplevel(self.parent_widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.configure(bg="#ffffff", relief="solid", bd=2)
        self.tooltip_window.wm_attributes("-topmost", True)
        
        # Calculate size based on content
        max_width = 500
        max_height = 400
        
        # Main frame
        main_frame = tk.Frame(self.tooltip_window, bg="#ffffff", padx=15, pady=12)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame, bg="#ffffff")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(
            header_frame,
            text="💡 Query Explanation",
            font=("Arial", 11, "bold"),
            bg="#ffffff",
            fg="#333333",
            anchor="w"
        )
        title_label.pack(side=tk.LEFT)
        
        # Close button
        close_btn = tk.Button(
            header_frame,
            text="×",
            font=("Arial", 14, "bold"),
            bg="#ffffff",
            fg="#666666",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=self.hide_tooltip,
            padx=5,
            pady=0
        )
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#000000", bg="#f0f0f0"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg="#666666", bg="#ffffff"))
        
        # Explanation text area with scrollbar
        text_frame = tk.Frame(main_frame, bg="#ffffff")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        explanation_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="#ffffff",
            fg="#000000",
            relief="flat",
            bd=0,
            padx=5,
            pady=5,
            yscrollcommand=scrollbar.set,
            width=60,
            height=15
        )
        explanation_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=explanation_text.yview)
        
        # Insert explanation
        explanation_text.insert("1.0", explanation)
        explanation_text.config(state=tk.DISABLED)
        
        # Update window size
        self.tooltip_window.update_idletasks()
        width = min(max_width, self.tooltip_window.winfo_reqwidth())
        height = min(max_height, self.tooltip_window.winfo_reqheight())
        
        # Position tooltip (adjust to keep on screen)
        screen_width = self.tooltip_window.winfo_screenwidth()
        screen_height = self.tooltip_window.winfo_screenheight()
        
        if x + width > screen_width:
            x = screen_width - width - 10
        if y + height > screen_height:
            y = screen_height - height - 10
        
        self.tooltip_window.wm_geometry(f"{width}x{height}+{x}+{y}")
        
        # Bind click outside to close
        self.tooltip_window.bind("<Button-1>", lambda e: self._check_close(e))
        self.tooltip_window.focus_set()
    
    def _check_close(self, event):
        """Check if click is outside tooltip and close if so."""
        if self.tooltip_window:
            # Get tooltip bounds
            x1 = self.tooltip_window.winfo_x()
            y1 = self.tooltip_window.winfo_y()
            x2 = x1 + self.tooltip_window.winfo_width()
            y2 = y1 + self.tooltip_window.winfo_height()
            
            # Check if click is outside
            click_x = event.x_root
            click_y = event.y_root
            
            if not (x1 <= click_x <= x2 and y1 <= click_y <= y2):
                self.hide_tooltip()
    
    def hide_tooltip(self):
        """Hide the tooltip."""
        if self.tooltip_window:
            try:
                self.tooltip_window.destroy()
            except:
                pass
            self.tooltip_window = None
    
    def attach_to_widget(self, widget, get_query_func):
        """
        Attach tooltip to a widget (e.g., explain button).
        
        Args:
            widget: The widget to attach to
            get_query_func: Function that returns the SQL query to explain
        """
        def show_explanation_on_hover(event=None):
            query = get_query_func()
            if query:
                x = widget.winfo_rootx() + widget.winfo_width() // 2
                y = widget.winfo_rooty() + widget.winfo_height() + 5
                self.show_explanation(query, x, y)
        
        def hide_on_leave(event=None):
            # Don't hide immediately - let user read
            pass
        
        # Bind to button click or hover
        widget.bind("<Button-1>", lambda e: show_explanation_on_hover(e))
        # Optionally bind to hover
        # widget.bind("<Enter>", lambda e: show_explanation_on_hover(e))
        # widget.bind("<Leave>", hide_on_leave)

