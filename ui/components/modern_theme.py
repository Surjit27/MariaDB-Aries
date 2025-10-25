import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap import Style

class ModernTheme:
    def __init__(self):
        self.style = Style()
        self.setup_modern_theme()
        
    def setup_modern_theme(self):
        """Setup the modern MariaDB:Aries theme."""
        # Create custom dark theme
        self.style.theme_use("darkly")
        
        # Configure main window
        self.style.configure("Main.TFrame", 
                           background="#1a1a1a", 
                           relief="flat")
        
        # Configure side navigation
        self.style.configure("SideNav.TFrame", 
                           background="#1e1e1e", 
                           relief="flat",
                           borderwidth=0)
        
        # Configure navigation buttons
        self.style.configure("Nav.TButton",
                           background="#1e1e1e",
                           foreground="#ffffff",
                           borderwidth=0,
                           focuscolor="none",
                           padding=(10, 8))
        
        self.style.map("Nav.TButton",
                      background=[("active", "#2d2d2d"),
                                ("pressed", "#404040")])
        
        # Configure main content area
        self.style.configure("Content.TFrame",
                           background="#1a1a1a",
                           relief="flat")
        
        # Configure SQL editor
        self.style.configure("SQL.TFrame",
                           background="#1a1a1a",
                           relief="flat")
        
        # Configure results viewer
        self.style.configure("Results.TFrame",
                           background="#1a1a1a",
                           relief="flat")
        
        # Configure header bar
        self.style.configure("Header.TFrame",
                           background="#2d2d2d",
                           relief="flat",
                           borderwidth=0)
        
        # Configure header buttons
        self.style.configure("Header.TButton",
                           background="#2d2d2d",
                           foreground="#ffffff",
                           borderwidth=0,
                           focuscolor="none",
                           padding=(8, 6))
        
        self.style.map("Header.TButton",
                      background=[("active", "#404040"),
                                ("pressed", "#555555")])
        
        # Configure AI prompt
        self.style.configure("AIPrompt.TFrame",
                           background="#1e1e1e",
                           relief="raised",
                           borderwidth=1)
        
        # Configure modals
        self.style.configure("Modal.TFrame",
                           background="#2d2d2d",
                           relief="raised",
                           borderwidth=2)
        
        # Configure modal buttons
        self.style.configure("Modal.TButton",
                           background="#404040",
                           foreground="#ffffff",
                           borderwidth=0,
                           padding=(12, 8))
        
        self.style.map("Modal.TButton",
                      background=[("active", "#555555"),
                                ("pressed", "#666666")])
        
        # Configure treeview for sidebar
        self.style.configure("Treeview",
                           background="#1e1e1e",
                           foreground="#ffffff",
                           fieldbackground="#1e1e1e",
                           borderwidth=0)
        
        self.style.configure("Treeview.Heading",
                           background="#404040",
                           foreground="#ffffff",
                           borderwidth=0)
        
        # Configure text widgets (using standard Frame style)
        # Note: Text widgets use standard tkinter styling, not ttk styles
        
        # Configure labels
        self.style.configure("Title.TLabel",
                           background="#1a1a1a",
                           foreground="#ffffff",
                           font=("Arial", 14, "bold"))
        
        self.style.configure("Subtitle.TLabel",
                           background="#1a1a1a",
                           foreground="#cccccc",
                           font=("Arial", 10))
        
        self.style.configure("Info.TLabel",
                           background="#1a1a1a",
                           foreground="#888888",
                           font=("Arial", 9))
        
        # Configure entry widgets
        self.style.configure("Modern.TEntry",
                           background="#404040",
                           foreground="#ffffff",
                           borderwidth=1,
                           relief="flat",
                           fieldbackground="#404040")
        
        # Configure text areas (using standard Text widget)
        # Note: Text widgets don't use ttk styles, they use tkinter styles
        
        # Configure scrollbars
        self.style.configure("Modern.TScrollbar",
                           background="#2d2d2d",
                           troughcolor="#1a1a1a",
                           borderwidth=0,
                           arrowcolor="#ffffff",
                           darkcolor="#2d2d2d",
                           lightcolor="#2d2d2d")
        
        # Configure separators
        self.style.configure("Modern.TSeparator",
                           background="#404040")
        
        # Configure notebook tabs
        self.style.configure("TNotebook",
                           background="#1e1e1e",
                           borderwidth=0)
        
        self.style.configure("TNotebook.Tab",
                           background="#1e1e1e",
                           foreground="#cccccc",
                           borderwidth=0,
                           padding=(12, 8))
        
        self.style.map("TNotebook.Tab",
                      background=[("selected", "#2d2d2d"),
                                ("active", "#404040")])
        
        # Modern notebook style
        self.style.configure("Modern.TNotebook",
                           background="#1e1e1e",
                           borderwidth=0)
        
        self.style.configure("Modern.TNotebook.Tab",
                           background="#1e1e1e",
                           foreground="#cccccc",
                           borderwidth=0,
                           padding=(12, 8),
                           font=("Consolas", 10))
        
        self.style.map("Modern.TNotebook.Tab",
                      background=[("selected", "#2d2d2d"),
                                ("active", "#404040")])
        
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
                           background="#2d2d2d",
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
            "primary": "#1e1e1e",      # Main background (VS Code dark)
            "secondary": "#252526",     # Sidebar background
            "accent": "#2d2d2d",       # Interactive elements
            "highlight": "#404040",     # Hover states
            "text_primary": "#cccccc",  # Primary text
            "text_secondary": "#ffffff", # Secondary text
            "text_muted": "#888888",   # Muted text
            "border": "#3c3c3c",       # Border color
            "success": "#4caf50",      # Success color
            "warning": "#ff9800",      # Warning color
            "error": "#f44747",        # Error color
            "info": "#007acc",         # Info color (VS Code blue)
            "keyword": "#569cd6",      # SQL keywords
            "string": "#ce9178",       # String literals
            "comment": "#6a9955",      # Comments
            "number": "#b5cea8",       # Numbers
            "function": "#dcdcaa"      # Functions
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
