import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap import Style

class ModernTheme:
    def __init__(self):
        self.style = Style()
        self.setup_modern_theme()
        
    def setup_modern_theme(self):
        """Setup the modern MariaDB:Aries theme."""
        # Use light theme (white mode)
        self.style.theme_use("flatly")
        
        # Configure main window
        self.style.configure("Main.TFrame", 
                           background="#ffffff", 
                           relief="flat")
        
        # Configure side navigation
        self.style.configure("SideNav.TFrame", 
                           background="#f8f9fa", 
                           relief="flat",
                           borderwidth=0)
        
        # Configure navigation buttons
        self.style.configure("Nav.TButton",
                           background="#f8f9fa",
                           foreground="#333333",
                           borderwidth=0,
                           focuscolor="none",
                           padding=(10, 8))
        
        self.style.map("Nav.TButton",
                      background=[("active", "#e9ecef"),
                                ("pressed", "#dee2e6")])
        
        # Configure main content area
        self.style.configure("Content.TFrame",
                           background="#ffffff",
                           relief="flat")
        
        # Configure SQL editor
        self.style.configure("SQL.TFrame",
                           background="#ffffff",
                           relief="flat")
        
        # Configure results viewer
        self.style.configure("Results.TFrame",
                           background="#ffffff",
                           relief="flat")
        
        # Configure header bar
        self.style.configure("Header.TFrame",
                           background="#ffffff",
                           relief="flat",
                           borderwidth=0)
        
        # Configure header buttons
        self.style.configure("Header.TButton",
                           background="#ffffff",
                           foreground="#333333",
                           borderwidth=0,
                           focuscolor="none",
                           padding=(8, 6))
        
        self.style.map("Header.TButton",
                      background=[("active", "#f0f0f0"),
                                ("pressed", "#e0e0e0")])
        
        # Configure AI prompt
        self.style.configure("AIPrompt.TFrame",
                           background="#f8f9fa",
                           relief="raised",
                           borderwidth=1)
        
        # Configure modals
        self.style.configure("Modal.TFrame",
                           background="#ffffff",
                           relief="raised",
                           borderwidth=2)
        
        # Configure modal buttons
        self.style.configure("Modal.TButton",
                           background="#007bff",
                           foreground="#ffffff",
                           borderwidth=0,
                           padding=(12, 8))
        
        self.style.map("Modal.TButton",
                      background=[("active", "#0056b3"),
                                ("pressed", "#004085")])
        
        # Configure treeview for sidebar
        self.style.configure("Treeview",
                           background="#ffffff",
                           foreground="#333333",
                           fieldbackground="#ffffff",
                           borderwidth=0)
        
        self.style.configure("Treeview.Heading",
                           background="#f8f9fa",
                           foreground="#333333",
                           borderwidth=0)
        
        # Configure text widgets (using standard Frame style)
        # Note: Text widgets use standard tkinter styling, not ttk styles
        
        # Configure labels
        self.style.configure("Title.TLabel",
                           background="#ffffff",
                           foreground="#333333",
                           font=("Arial", 14, "bold"))
        
        self.style.configure("Subtitle.TLabel",
                           background="#ffffff",
                           foreground="#666666",
                           font=("Arial", 10))
        
        self.style.configure("Info.TLabel",
                           background="#ffffff",
                           foreground="#888888",
                           font=("Arial", 9))
        
        # Configure entry widgets
        self.style.configure("Modern.TEntry",
                           background="#ffffff",
                           foreground="#333333",
                           borderwidth=1,
                           relief="solid",
                           fieldbackground="#ffffff")
        
        # Configure text areas (using standard Text widget)
        # Note: Text widgets don't use ttk styles, they use tkinter styles
        
        # Configure scrollbars
        self.style.configure("Modern.TScrollbar",
                           background="#e0e0e0",
                           troughcolor="#f8f9fa",
                           borderwidth=0,
                           arrowcolor="#333333",
                           darkcolor="#e0e0e0",
                           lightcolor="#e0e0e0")
        
        # Configure separators
        self.style.configure("Modern.TSeparator",
                           background="#e0e0e0")
        
        # Configure notebook tabs
        self.style.configure("TNotebook",
                           background="#ffffff",
                           borderwidth=0)
        
        self.style.configure("TNotebook.Tab",
                           background="#f8f9fa",
                           foreground="#333333",
                           borderwidth=0,
                           padding=(12, 8))
        
        self.style.map("TNotebook.Tab",
                      background=[("selected", "#ffffff"),
                                ("active", "#e9ecef")])
        
        # Modern notebook style
        self.style.configure("Modern.TNotebook",
                           background="#ffffff",
                           borderwidth=0)
        
        self.style.configure("Modern.TNotebook.Tab",
                           background="#f8f9fa",
                           foreground="#333333",
                           borderwidth=0,
                           padding=(12, 8),
                           font=("Consolas", 10))
        
        self.style.map("Modern.TNotebook.Tab",
                      background=[("selected", "#ffffff"),
                                ("active", "#e9ecef")])
        
        # Configure listbox (using standard Listbox style)
        # Note: Listbox widgets use standard tkinter styling
        
        # Configure combobox (using standard Combobox style)
        # Note: Custom styles may not be supported by all ttkbootstrap versions
        
        # Configure checkbutton (using standard Checkbutton style)
        # Note: Custom styles may not be supported by all ttkbootstrap versions
        
        # Configure radiobutton (using standard Radiobutton style)
        # Note: Custom styles may not be supported by all ttkbootstrap versions
        
        # Configure progressbar (using standard Progressbar style)
        # Note: Custom styles may not be supported by all ttkbootstrap versions
        
        # Configure tooltip
        self.style.configure("Tooltip.TLabel",
                           background="#333333",
                           foreground="#ffffff",
                           font=("Arial", 9),
                           relief="raised",
                           borderwidth=1)
    
    def get_emoji_icons(self):
        """Get colored emoji icons for the interface."""
        return {
            # Navigation icons
            "database": "🗄️",
            "table": "📊", 
            "function": "⚡",
            "view": "👁️",
            "trigger": "🔧",
            "procedure": "📝",
            "index": "📇",
            "constraint": "🔗",
            
            # Action icons
            "create": "➕",
            "edit": "✏️",
            "delete": "🗑️",
            "run": "▶️",
            "stop": "⏹️",
            "refresh": "🔄",
            "save": "💾",
            "load": "📂",
            "export": "📤",
            "import": "📥",
            "copy": "📋",
            "paste": "📄",
            "cut": "✂️",
            "undo": "↶",
            "redo": "↷",
            
            # AI icons
            "ai_generate": "🤖",
            "ai_optimize": "⚡",
            "ai_explain": "💡",
            "ai_suggest": "💭",
            
            # Status icons
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
            "loading": "⏳",
            "done": "🎉",
            
            # Navigation arrows
            "expand": "▶",
            "collapse": "▼",
            "up": "↑",
            "down": "↓",
            "left": "←",
            "right": "→",
            
            # Special icons
            "settings": "⚙️",
            "help": "❓",
            "about": "ℹ️",
            "theme": "🌙",
            "search": "🔍",
            "filter": "🔽",
            "sort": "🔀",
            "group": "📁",
            "link": "🔗",
            "unlink": "🔓",
            "lock": "🔒",
            "unlock": "🔓"
        }
    
    def get_color_scheme(self):
        """Get the color scheme for the interface."""
        return {
            "primary": "#ffffff",      # Main background (white)
            "secondary": "#f8f9fa",     # Sidebar background
            "accent": "#e9ecef",       # Interactive elements
            "highlight": "#dee2e6",    # Hover states
            "text_primary": "#333333",  # Primary text
            "text_secondary": "#212529", # Secondary text
            "text_muted": "#6c757d",   # Muted text
            "border": "#dee2e6",       # Border color
            "success": "#28a745",       # Success color
            "warning": "#ffc107",       # Warning color
            "error": "#dc3545",         # Error color
            "info": "#007bff",          # Info color (bootstrap blue)
            "keyword": "#0066cc",       # SQL keywords
            "string": "#cc6600",        # String literals
            "comment": "#6c757d",      # Comments
            "number": "#006600",        # Numbers
            "function": "#0099ff"       # Functions
        }
    
    def apply_modern_theme(self, widget):
        """Apply modern theme to a widget."""
        if isinstance(widget, ttk.Frame):
            widget.configure(style="Main.TFrame")
        elif isinstance(widget, ttk.Button):
            widget.configure(style="Nav.TButton")
        elif isinstance(widget, ttk.Label):
            widget.configure(style="Title.TLabel")
        elif isinstance(widget, ttk.Entry):
            widget.configure(style="Modern.TEntry")
        elif isinstance(widget, ttk.Text):
            widget.configure(style="Modern.TText")
        
        # Apply to children
        for child in widget.winfo_children():
            self.apply_modern_theme(child)
