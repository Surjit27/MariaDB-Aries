import tkinter as tk
import ttkbootstrap as ttk
import sys
import os
import re
import threading
import time

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ui.components.modern_theme import ModernTheme
from sql_engine.simple_sql_compiler import SimpleSQLCompiler
from ai.ai_pipeline import AIPipeline
from ui.components.horizontal_ai_modal import HorizontalAIModal

class EnhancedSQLEditor:
    def __init__(self, parent, db_manager, ai_integration):
        self.parent = parent
        self.db_manager = db_manager
        self.ai_integration = ai_integration
        self.theme = ModernTheme()
        self.icons = self.theme.get_emoji_icons()
        self.syntax_highlighting = True
        self.minimap_visible = True
        self.ai_autocomplete = True
        self.autocomplete_suggestions = []
        self.suggestion_window = None
        
        # Store current query results for dashboard
        self.current_query = ""
        self.current_query_columns = []
        self.current_query_data = []
        
        # Initialize SQL compiler
        self.sql_compiler = SimpleSQLCompiler()
        
        # Initialize AI Pipeline
        api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyCcY01MZsIFwm1li0IAf_pk5knwo6emVjo')
        self.ai_pipeline = AIPipeline(db_manager, api_key)
        
        
        # Horizontal AI Modal (will be initialized when needed)
        self.horizontal_ai_modal = None
        
        # Dashboard panel reference (set from main)
        self.dashboard_panel = None
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create the enhanced SQL editor."""
        # Main editor frame
        self.editor_frame = ttk.Frame(self.parent, style="SQL.TFrame")
        self.editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create toolbar
        self.create_toolbar()
        
        # Create editor area
        self.create_editor_area()
        
        # Create status bar
        self.create_status_bar()
        
    def create_toolbar(self):
        """Create the editor toolbar."""
        toolbar_frame = ttk.Frame(self.editor_frame, style="SQL.TFrame")
        toolbar_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Toolbar buttons with improved icons
        self.create_toolbar_button(toolbar_frame, "▶", "Run Query", self.run_query, "Run SQL (Ctrl+R)")
        self.create_toolbar_button(toolbar_frame, "⚙", "Compile", self.compile_sql, "Compile SQL (Ctrl+Shift+C)")
        self.create_toolbar_button(toolbar_frame, "🗑", "Clear", self.clear_editor, "Clear Editor (Ctrl+C)")
        self.create_toolbar_button(toolbar_frame, "✨", "AI Generate", self.generate_sql, "AI Generate (Ctrl+G)")
        self.create_toolbar_button(toolbar_frame, "💬", "AI Chat", self.show_horizontal_ai_modal, "AI Chat Assistant (Ctrl+Shift+A)")
        self.create_toolbar_button(toolbar_frame, "💡", "Explain", self.explain_sql, "Explain SQL")
        
        # Separator
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Dashboard button with purple highlight
        dashboard_btn = tk.Button(toolbar_frame, 
                                  text="📊", 
                                  command=self.generate_dashboard,
                                  bg="#8B5CF6",  # Purple background
                                  fg="white",    # White text
                                  font=("Segoe UI Emoji", 12),
                                  width=3, height=1,
                                  activebackground="#7C3AED",  # Darker purple on hover
                                  activeforeground="white",
                                  relief="flat",
                                  cursor="hand2",
                                  padx=4, pady=2,
                                  highlightthickness=0,
                                  borderwidth=1,
                                  highlightbackground="#8B5CF6",
                                  highlightcolor="#7C3AED")
        # Subtle hover effect
        def on_enter_dashboard(e):
            dashboard_btn.configure(bg="#7C3AED", highlightbackground="#7C3AED")
        def on_leave_dashboard(e):
            dashboard_btn.configure(bg="#8B5CF6", highlightbackground="#8B5CF6")
        dashboard_btn.bind("<Enter>", on_enter_dashboard)
        dashboard_btn.bind("<Leave>", on_leave_dashboard)
        dashboard_btn.pack(side=tk.LEFT, padx=3)
        self.create_tooltip(dashboard_btn, "Generate Dashboard with AI")
        
        # Separator
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Editor options with improved icons
        self.create_toolbar_button(toolbar_frame, "🎨", "Syntax", self.toggle_syntax, "Toggle Syntax Highlighting")
        self.create_toolbar_button(toolbar_frame, "🗺", "Minimap", self.toggle_minimap, "Toggle Minimap")
        self.create_toolbar_button(toolbar_frame, "⚡", "AI Auto", self.toggle_ai_autocomplete, "Toggle AI Autocomplete")
        
        # Separator
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Line numbers
        self.line_numbers = tk.Text(toolbar_frame, width=4, height=1, 
                                   bg="#1e1e1e", fg="#888888", 
                                   font=("Consolas", 11), state=tk.DISABLED,
                                   relief="flat", bd=0)
        self.line_numbers.pack(side=tk.RIGHT, padx=5)
        
    def create_toolbar_button(self, parent, emoji, tooltip, command, full_tooltip):
        """Create a modern, clear toolbar button with improved icons."""
        # All buttons with consistent modern clear design
        btn = tk.Button(parent, text=emoji, command=command,
                       bg="#f8f9fa", fg="#333333", bd=1,
                       font=("Segoe UI Emoji", 12),
                       width=3, height=1,
                       activebackground="#e9ecef", 
                       activeforeground="#000000",
                       relief="flat",
                       cursor="hand2",
                       padx=4, pady=2,
                       highlightthickness=0,
                       borderwidth=1,
                       highlightbackground="#dee2e6",
                       highlightcolor="#007acc")
        # Subtle hover effect
        def on_enter(e):
            btn.configure(bg="#e9ecef", bd=1)
        def on_leave(e):
            btn.configure(bg="#f8f9fa", bd=1)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        btn.pack(side=tk.LEFT, padx=3)
        
        # Add tooltip
        self.create_tooltip(btn, full_tooltip)
        return btn
    
    def create_editor_area(self):
        """Create the main editor area."""
        # Editor container
        editor_container = ttk.Frame(self.editor_frame, style="SQL.TFrame")
        editor_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # Create paned window for editor and minimap
        if self.minimap_visible:
            self.paned_window = ttk.PanedWindow(editor_container, orient=tk.HORIZONTAL)
            self.paned_window.pack(fill=tk.BOTH, expand=True)
            
            # Main editor
            self.create_main_editor()
            
            # Minimap
            self.create_minimap()
            
            # Add to paned window
            self.paned_window.add(self.editor_widget, weight=3)
            self.paned_window.add(self.minimap_widget, weight=1)
        else:
            # Just the main editor
            self.create_main_editor()
            self.editor_widget.pack(fill=tk.BOTH, expand=True)
    
    def create_main_editor(self):
        """Create the main SQL editor."""
        # Editor frame
        editor_frame = ttk.Frame(self.paned_window if self.minimap_visible else self.editor_frame, 
                                style="SQL.TFrame")
        
        # Create text widget with enhanced styling
        self.editor = tk.Text(editor_frame,
                             font=("Consolas", 12),
                             bg="#1e1e1e", fg="#ffffff",
                             insertbackground="#ffffff",
                             selectbackground="#404040",
                             selectforeground="#ffffff",
                             relief="flat", bd=1,
                             wrap=tk.NONE,
                             undo=True,
                             maxundo=50)
        
        # Configure tags for syntax highlighting
        self.configure_syntax_highlighting()
        
        # Bind events
        self.editor.bind("<KeyRelease>", self.on_key_release)
        self.editor.bind("<KeyPress>", self.on_key_press)
        self.editor.bind("<Button-1>", self.on_click)
        self.editor.bind("<FocusIn>", self.on_focus_in)
        self.editor.bind("<FocusOut>", self.on_focus_out)
        self.editor.bind("<Button-3>", self.on_right_click)  # Right-click for AI popup
        # Bind Ctrl+/ for toggle highlight
        self.editor.bind("<Control-slash>", lambda e: self.toggle_highlight())
        self.editor.bind("<Control-question>", lambda e: self.toggle_highlight())  # Alternative binding
        
        # Scrollbar for editor
        editor_scrollbar = ttk.Scrollbar(editor_frame, orient=tk.VERTICAL, command=self.editor.yview)
        self.editor.configure(yscrollcommand=editor_scrollbar.set)
        
        # Pack editor and scrollbar
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        editor_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.editor_widget = editor_frame
    
    def create_minimap(self):
        """Create the minimap widget."""
        minimap_frame = ttk.Frame(self.paned_window, style="SQL.TFrame")
        
        # Minimap text widget
        self.minimap = tk.Text(minimap_frame,
                              font=("Consolas", 2),
                              bg="#1e1e1e", fg="#888888",
                              relief="flat", bd=1,
                              wrap=tk.NONE,
                              state=tk.DISABLED,
                              width=20)
        
        # Minimap scrollbar
        minimap_scrollbar = ttk.Scrollbar(minimap_frame, orient=tk.VERTICAL, command=self.minimap.yview)
        self.minimap.configure(yscrollcommand=minimap_scrollbar.set)
        
        # Pack minimap
        self.minimap.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        minimap_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.minimap_widget = minimap_frame
        
        # Bind minimap events
        self.minimap.bind("<Button-1>", self.on_minimap_click)
        self.minimap.bind("<B1-Motion>", self.on_minimap_drag)
    
    def create_status_bar(self):
        """Create the status bar."""
        status_frame = ttk.Frame(self.editor_frame, style="SQL.TFrame")
        status_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Status labels
        self.status_label = ttk.Label(status_frame, text="Ready", style="Info.TLabel")
        self.status_label.pack(side=tk.LEFT)
        
        self.cursor_label = ttk.Label(status_frame, text="Line 1, Col 1", style="Info.TLabel")
        self.cursor_label.pack(side=tk.RIGHT)
        
        # Update cursor position
        self.editor.bind("<KeyRelease>", self.update_cursor_position)
        self.editor.bind("<Button-1>", self.update_cursor_position)
    
    def configure_syntax_highlighting(self):
        """Configure syntax highlighting tags."""
        # SQL keywords
        keywords = [
            'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER',
            'TABLE', 'DATABASE', 'INDEX', 'VIEW', 'TRIGGER', 'FUNCTION', 'PROCEDURE',
            'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN', 'IS', 'NULL', 'ORDER', 'BY',
            'GROUP', 'HAVING', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON',
            'UNION', 'DISTINCT', 'LIMIT', 'OFFSET', 'ASC', 'DESC', 'AS', 'CASE',
            'WHEN', 'THEN', 'ELSE', 'END', 'IF', 'EXISTS', 'ALL', 'ANY', 'SOME'
        ]
        
        # Configure tags
        self.editor.tag_configure("keyword", foreground="#569cd6", font=("Consolas", 12, "bold"))
        self.editor.tag_configure("string", foreground="#ce9178")
        self.editor.tag_configure("comment", foreground="#6a9955", font=("Consolas", 12, "italic"))
        self.editor.tag_configure("number", foreground="#b5cea8")
        self.editor.tag_configure("operator", foreground="#d4d4d4")
        self.editor.tag_configure("function", foreground="#dcdcaa")
        self.editor.tag_configure("error", foreground="#f44747", background="#2d2d2d")
        
        # Configure highlight tag for manual highlighting
        self.editor.tag_configure("manual_highlight", 
                                 background="#ffeb3b", 
                                 foreground="#000000",
                                 relief="raised",
                                 borderwidth=1)
        
        # Store keywords for highlighting
        self.sql_keywords = keywords
    
    def on_key_release(self, event):
        """Handle key release event."""
        if self.syntax_highlighting:
            self.highlight_syntax()
        
        if self.ai_autocomplete and self.ai_integration:
            self.check_autocomplete()
        
        self.update_cursor_position()
        self.update_minimap()
    
    def on_key_press(self, event):
        """Handle key press event."""
        # Remove accepted highlight if user starts editing (typing, deleting, etc.)
        if event.keysym not in ["Up", "Down", "Left", "Right", "Home", "End", "Page_Up", "Page_Down", 
                               "Tab", "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
                               "Escape", "Return", "Enter"]:
            # User is typing/editing - remove accepted highlight if it exists
            try:
                if hasattr(self, 'horizontal_ai_modal') and self.horizontal_ai_modal:
                    if hasattr(self.horizontal_ai_modal, 'remove_accepted_highlight'):
                        self.horizontal_ai_modal.remove_accepted_highlight()
            except Exception:
                pass
        
        # Handle Tab key for autocomplete
        if event.keysym == "Tab" and self.suggestion_window:
            self.accept_suggestion()
            return "break"
        
        # Handle Escape key to hide suggestions
        if event.keysym == "Escape":
            self.hide_suggestions()
            return "break"
        
        # Handle Ctrl+R for run
        if event.state & 0x4 and event.keysym == "r":  # Ctrl+R
            self.run_query()
            return "break"
        
        # Handle Ctrl+C for clear
        if event.state & 0x4 and event.keysym == "c":  # Ctrl+C
            self.clear_editor()
            return "break"
        
        # Handle Ctrl+G for AI generate
        if event.state & 0x4 and event.keysym == "g":  # Ctrl+G
            self.generate_sql()
            return "break"
        
        # Handle Ctrl+Shift+C for compile
        if event.state & 0x5 and event.keysym == "c":  # Ctrl+Shift+C
            self.compile_sql()
            return "break"
        
        # Handle Ctrl+Shift+A for horizontal AI modal
        if event.state & 0x5 and event.keysym == "a":  # Ctrl+Shift+A
            self.show_horizontal_ai_modal()
            return "break"
    
    def on_click(self, event):
        """Handle click event."""
        self.update_cursor_position()
        
        # Remove accepted highlight if user clicks to edit elsewhere
        try:
            if hasattr(self, 'horizontal_ai_modal') and self.horizontal_ai_modal:
                if hasattr(self.horizontal_ai_modal, 'remove_accepted_highlight'):
                    # Only remove if cursor is outside the accepted range
                    cursor_pos = self.editor.index(tk.INSERT)
                    accepted_ranges = self.editor.tag_ranges("ai_accepted")
                    is_in_accepted = False
                    for i in range(0, len(accepted_ranges), 2):
                        if len(accepted_ranges) > i + 1:
                            start = self.editor.index(accepted_ranges[i])
                            end = self.editor.index(accepted_ranges[i + 1])
                            if self.editor.compare(cursor_pos, ">=", start) and self.editor.compare(cursor_pos, "<=", end):
                                is_in_accepted = True
                                break
                    if not is_in_accepted:
                        self.horizontal_ai_modal.remove_accepted_highlight()
        except Exception:
            pass
    
    def on_focus_in(self, event):
        """Handle focus in event."""
        self.status_label.configure(text="Editing")
    
    def on_focus_out(self, event):
        """Handle focus out event."""
        self.status_label.configure(text="Ready")
    
    def on_right_click(self, event):
        """Handle right-click event for context menu."""
        self.show_context_menu(event)
    
    def show_context_menu(self, event):
        """Show right-click context menu."""
        # Create context menu
        context_menu = tk.Menu(self.editor, tearoff=0)
        
        # Edit operations
        context_menu.add_command(label="📋 Copy", command=self.copy_text, accelerator="Ctrl+C")
        context_menu.add_command(label="📄 Paste", command=self.paste_text, accelerator="Ctrl+V")
        context_menu.add_command(label="✂️ Cut", command=self.cut_text, accelerator="Ctrl+X")
        context_menu.add_separator()
        
        # Undo/Redo
        context_menu.add_command(label="↶ Undo", command=self.undo_text, accelerator="Ctrl+Z")
        context_menu.add_command(label="↷ Redo", command=self.redo_text, accelerator="Ctrl+Y")
        context_menu.add_separator()
        
        # Selection operations
        context_menu.add_command(label="🔍 Select All", command=self.select_all, accelerator="Ctrl+A")
        context_menu.add_command(label="🔍 Find", command=self.find_text, accelerator="Ctrl+F")
        context_menu.add_command(label="🖍️ Toggle Highlight", command=self.toggle_highlight, accelerator="Ctrl+/")
        context_menu.add_separator()
        
        # AI operations
        context_menu.add_command(label="💬 AI Chat Assistant", command=lambda: self.show_horizontal_ai_modal())
        context_menu.add_command(label="💡 AI Explain", command=self.ai_explain)
        context_menu.add_command(label="🔧 AI Optimize", command=self.ai_optimize_query)
        context_menu.add_separator()
        
        # SQL operations
        context_menu.add_command(label="▶️ Run Query", command=self.run_query, accelerator="Ctrl+R")
        context_menu.add_command(label="🧹 Clear", command=self.clear_editor, accelerator="Ctrl+Shift+C")
        context_menu.add_command(label="🎨 Format SQL", command=self.format_sql)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def copy_text(self):
        """Copy selected text."""
        try:
            self.editor.event_generate("<<Copy>>")
        except:
            pass
    
    def paste_text(self):
        """Paste text."""
        try:
            self.editor.event_generate("<<Paste>>")
        except:
            pass
    
    def cut_text(self):
        """Cut selected text."""
        try:
            self.editor.event_generate("<<Cut>>")
        except:
            pass
    
    def undo_text(self):
        """Undo last action."""
        try:
            self.editor.event_generate("<<Undo>>")
        except:
            pass
    
    def redo_text(self):
        """Redo last action."""
        try:
            self.editor.event_generate("<<Redo>>")
        except:
            pass
    
    def select_all(self):
        """Select all text."""
        try:
            self.editor.tag_add(tk.SEL, "1.0", tk.END)
            self.editor.mark_set(tk.INSERT, "1.0")
            self.editor.see(tk.INSERT)
        except:
            pass
    
    def find_text(self):
        """Find text in editor."""
        from tkinter import simpledialog
        search_text = simpledialog.askstring("Find", "Enter text to find:")
        if search_text:
            # Simple find implementation
            content = self.editor.get("1.0", tk.END)
            if search_text.lower() in content.lower():
                self.status_label.configure(text=f"Found '{search_text}'")
            else:
                self.status_label.configure(text=f"'{search_text}' not found")
    
    def get_query_for_ai(self):
        """Get highlighted query or all query text for AI operations.
        Returns tuple: (query_text, is_highlighted)"""
        try:
            # Check for highlighted text first
            highlight_ranges = self.editor.tag_ranges("manual_highlight")
            
            if highlight_ranges:
                # Extract all highlighted text segments and combine them
                highlighted_segments = []
                for i in range(0, len(highlight_ranges), 2):
                    start = self.editor.index(highlight_ranges[i])
                    end = self.editor.index(highlight_ranges[i + 1])
                    segment = self.editor.get(start, end)
                    if segment.strip():
                        highlighted_segments.append(segment.strip())
                
                if highlighted_segments:
                    # Combine all highlighted segments with newlines
                    combined_query = "\n".join(highlighted_segments)
                    return combined_query, True
            
            # No highlighted text, return all editor content
            all_text = self.editor.get("1.0", tk.END).strip()
            return all_text, False
            
        except Exception as e:
            # Fallback to all text on error
            all_text = self.editor.get("1.0", tk.END).strip()
            return all_text, False
    
    def toggle_highlight(self):
        """Toggle highlight on selected text or current line if no selection."""
        try:
            # Get selection if exists
            if self.editor.tag_ranges(tk.SEL):
                start = self.editor.index(tk.SEL_FIRST)
                end = self.editor.index(tk.SEL_LAST)
                has_selection = True
            else:
                # If no selection, highlight current line
                current_line = self.editor.index(tk.INSERT)
                line_start = current_line.split('.')[0] + '.0'
                line_end = current_line.split('.')[0] + '.end'
                start = line_start
                end = line_end
                has_selection = False
            
            # Check if any part of the selected range has the highlight tag
            highlight_ranges = self.editor.tag_ranges("manual_highlight")
            is_highlighted = False
            
            # Check if the start position is within any highlight range
            for i in range(0, len(highlight_ranges), 2):
                highlight_start = self.editor.index(highlight_ranges[i])
                highlight_end = self.editor.index(highlight_ranges[i + 1])
                
                # Check if our range overlaps with this highlight
                if (self.editor.compare(start, ">=", highlight_start) and 
                    self.editor.compare(start, "<=", highlight_end)) or \
                   (self.editor.compare(end, ">=", highlight_start) and 
                    self.editor.compare(end, "<=", highlight_end)) or \
                   (self.editor.compare(start, "<=", highlight_start) and 
                    self.editor.compare(end, ">=", highlight_end)):
                    is_highlighted = True
                    break
            
            if is_highlighted:
                # Remove highlight from the range
                self.editor.tag_remove("manual_highlight", start, end)
                if has_selection:
                    self.status_label.configure(text="Highlight removed")
                else:
                    self.status_label.configure(text="Line highlight removed")
            else:
                # Add highlight
                self.editor.tag_add("manual_highlight", start, end)
                # Move cursor to end to see the highlight better
                if not has_selection:
                    # Temporarily show selection
                    self.editor.tag_add(tk.SEL, start, end)
                    self.editor.after(200, lambda: self.editor.tag_remove(tk.SEL, start, end))
                self.editor.mark_set(tk.INSERT, end)
                self.editor.see(tk.INSERT)
                if has_selection:
                    self.status_label.configure(text="Text highlighted")
                else:
                    self.status_label.configure(text="Line highlighted")
                
        except Exception as e:
            self.status_label.configure(text="Error toggling highlight")
            print(f"Error in toggle_highlight: {e}")
    
    
    def ai_optimize_query(self):
        """Optimize highlighted query or all query using AI."""
        query, is_highlighted = self.get_query_for_ai()
        
        if query and self.ai_pipeline.is_available():
            # Show horizontal AI modal with optimization prompt
            self.show_horizontal_ai_modal()
            # Pre-fill with optimization prompt
            if hasattr(self.horizontal_ai_modal, 'input_entry'):
                self.horizontal_ai_modal.input_entry.delete(0, tk.END)
                query_label = "highlighted query" if is_highlighted else "query"
                self.horizontal_ai_modal.input_entry.insert(0, f"Optimize this {query_label} for better performance:\n\n{query}")
        else:
            self.status_label.configure(text="Please highlight or write a query to optimize")
    
    def ai_explain(self):
        """Explain highlighted SQL or all SQL."""
        query, is_highlighted = self.get_query_for_ai()
        
        if query:
            # Show horizontal AI modal with explanation prompt
            self.show_horizontal_ai_modal()
            # Pre-fill with explanation prompt
            if hasattr(self.horizontal_ai_modal, 'input_entry'):
                self.horizontal_ai_modal.input_entry.delete(0, tk.END)
                query_label = "highlighted SQL query" if is_highlighted else "SQL query"
                self.horizontal_ai_modal.input_entry.insert(0, f"Explain this {query_label}:\n\n{query}")
        else:
            self.status_label.configure(text="Please highlight or write SQL text to explain")
    
    def format_sql(self):
        """Format SQL code."""
        try:
            # Simple SQL formatting
            content = self.editor.get("1.0", tk.END)
            # Basic formatting - add newlines after keywords
            formatted = content.replace("SELECT", "\nSELECT")
            formatted = formatted.replace("FROM", "\nFROM")
            formatted = formatted.replace("WHERE", "\nWHERE")
            formatted = formatted.replace("ORDER BY", "\nORDER BY")
            formatted = formatted.replace("GROUP BY", "\nGROUP BY")
            formatted = formatted.replace("HAVING", "\nHAVING")
            
            self.editor.delete("1.0", tk.END)
            self.editor.insert("1.0", formatted.strip())
            self.status_label.configure(text="SQL formatted")
        except:
            self.status_label.configure(text="Error formatting SQL")
    
    def highlight_syntax(self):
        """Apply syntax highlighting to the editor."""
        # Get current content
        content = self.editor.get("1.0", tk.END)
        
        # Clear existing tags
        self.editor.tag_remove("keyword", "1.0", tk.END)
        self.editor.tag_remove("string", "1.0", tk.END)
        self.editor.tag_remove("comment", "1.0", tk.END)
        self.editor.tag_remove("number", "1.0", tk.END)
        self.editor.tag_remove("operator", "1.0", tk.END)
        self.editor.tag_remove("function", "1.0", tk.END)
        
        # Highlight keywords
        for keyword in self.sql_keywords:
            self.highlight_pattern(f"\\b{keyword}\\b", "keyword")
        
        # Highlight strings
        self.highlight_pattern(r"'[^']*'", "string")
        self.highlight_pattern(r'"[^"]*"', "string")
        
        # Highlight comments
        self.highlight_pattern(r"--.*$", "comment")
        self.highlight_pattern(r"/\*.*?\*/", "comment")
        
        # Highlight numbers
        self.highlight_pattern(r"\b\d+\.?\d*\b", "number")
        
        # Highlight operators
        self.highlight_pattern(r"[+\-*/=<>!]+", "operator")
        
        # Highlight functions
        self.highlight_pattern(r"\b\w+\s*\(", "function")
    
    def highlight_pattern(self, pattern, tag):
        """Highlight a specific pattern with a tag."""
        content = self.editor.get("1.0", tk.END)
        for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.editor.tag_add(tag, start, end)
    
    def check_autocomplete(self):
        """Check for autocomplete suggestions."""
        # Get current cursor position and text
        cursor_pos = self.editor.index(tk.INSERT)
        line_start = f"{cursor_pos.split('.')[0]}.0"
        current_line = self.editor.get(line_start, cursor_pos)
        
        # Check if we need suggestions
        if current_line.strip() and not current_line.endswith(' '):
            # Get suggestions from AI
            suggestions = self.ai_integration.get_suggestions(current_line)
            if suggestions:
                self.show_autocomplete_suggestions(suggestions, cursor_pos)
    
    def show_autocomplete_suggestions(self, suggestions, cursor_pos):
        """Show autocomplete suggestions."""
        if self.suggestion_window and self.suggestion_window.winfo_exists():
            self.suggestion_window.destroy()
        
        # Get cursor position
        x, y = self.editor.bbox(cursor_pos)
        if x is None or y is None:
            return
        
        # Create suggestions window
        self.suggestion_window = tk.Toplevel(self.editor)
        self.suggestion_window.wm_overrideredirect(True)
        self.suggestion_window.wm_geometry(f"+{self.editor.winfo_rootx() + x}+{self.editor.winfo_rooty() + y + 20}")
        self.suggestion_window.configure(bg="#2d2d2d")
        
        # Create suggestions list
        suggestions_frame = tk.Frame(self.suggestion_window, bg="#2d2d2d", relief="raised", bd=1)
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
        
        # Bind events
        self.suggestion_window.bind("<FocusOut>", lambda e: self.hide_suggestions())
        self.suggestion_window.bind("<Escape>", lambda e: self.hide_suggestions())
    
    def hide_suggestions(self):
        """Hide autocomplete suggestions."""
        if self.suggestion_window and self.suggestion_window.winfo_exists():
            self.suggestion_window.destroy()
            self.suggestion_window = None
    
    def accept_suggestion(self):
        """Accept the first suggestion."""
        if self.suggestion_buttons:
            first_btn = self.suggestion_buttons[0]
            suggestion = first_btn.cget("text")
            self.insert_suggestion(suggestion)
    
    def insert_suggestion(self, suggestion):
        """Insert suggestion into editor."""
        # Get current cursor position
        cursor_pos = self.editor.index(tk.INSERT)
        
        # Insert suggestion
        self.editor.insert(cursor_pos, suggestion)
        
        # Hide suggestions
        self.hide_suggestions()
    
    def update_cursor_position(self, event=None):
        """Update cursor position display."""
        cursor_pos = self.editor.index(tk.INSERT)
        line, col = cursor_pos.split('.')
        self.cursor_label.configure(text=f"Line {line}, Col {int(col) + 1}")
    
    def update_minimap(self):
        """Update the minimap."""
        if not self.minimap_visible:
            return
        
        # Get editor content
        content = self.editor.get("1.0", tk.END)
        
        # Update minimap
        self.minimap.configure(state=tk.NORMAL)
        self.minimap.delete("1.0", tk.END)
        self.minimap.insert("1.0", content)
        self.minimap.configure(state=tk.DISABLED)
    
    def on_minimap_click(self, event):
        """Handle minimap click."""
        # Calculate which line was clicked
        line_height = 12  # Approximate line height
        clicked_line = int(event.y / line_height) + 1
        
        # Jump to that line in the main editor
        self.editor.see(f"{clicked_line}.0")
    
    def on_minimap_drag(self, event):
        """Handle minimap drag."""
        self.on_minimap_click(event)
    
    def run_query(self):
        """Run the SQL query."""
        query = self.editor.get("1.0", tk.END).strip()
        if not query:
            self.status_label.configure(text="No query to run")
            return
        
        # Check for database creation/switching commands
        query_upper = query.upper()
        if query_upper.startswith('CREATE DATABASE'):
            self._handle_create_database(query)
            return
        elif query_upper.startswith('USE '):
            self._handle_use_database(query)
            return
        
        self.status_label.configure(text="Compiling and running query...")
        
        try:
            # Compile the SQL query using the SQL compiler
            compiled_query = self.sql_compiler.compile_sql(query)
            
            # Validate the compiled SQL
            validation_result = self.sql_compiler.validate_sql(compiled_query)
            
            if not validation_result['valid']:
                error_msg = f"SQL Error: {', '.join(validation_result['errors'])}"
                self.status_label.configure(text=error_msg)
                # Show error in results viewer if available
                if hasattr(self, 'results_viewer') and self.results_viewer:
                    self.results_viewer.display_error(error_msg)
                return
            
            # Show warnings if any
            if validation_result['warnings']:
                warning_msg = f"Warnings: {', '.join(validation_result['warnings'])}"
                self.status_label.configure(text=warning_msg)
            
            # Execute the compiled query through the database manager
            if self.db_manager and self.db_manager.current_db:
                try:
                    # Execute the query
                    result = self.db_manager.execute_query(compiled_query)
                    
                    # Display results in the results viewer
                    if hasattr(self, 'results_viewer') and self.results_viewer:
                        if isinstance(result, tuple) and len(result) == 3:
                            # Result is (columns, data, error) from database manager
                            columns, data, error = result
                            if error:
                                # If there's an error, show it
                                self.results_viewer.display_error(error)
                            elif columns and data is not None:
                                # Display the actual table data
                                self.results_viewer.display_results(columns, data)
                                # Store query results for dashboard
                                self.current_query = query
                                self.current_query_columns = columns
                                self.current_query_data = data
                                # Update dashboard if available
                                if hasattr(self, 'dashboard_panel') and self.dashboard_panel:
                                    self.dashboard_panel.set_query_results(query, columns, data)
                            else:
                                # No data returned (e.g., INSERT, UPDATE, DELETE)
                                self.results_viewer.display_results(['Message'], [['Query executed successfully']])
                                # Clear dashboard data for non-SELECT queries
                                self.current_query = ""
                                self.current_query_columns = []
                                self.current_query_data = []
                        elif isinstance(result, tuple) and len(result) == 2:
                            # Result is (columns, data) - legacy format
                            columns, data = result
                            self.results_viewer.display_results(columns, data)
                        else:
                            # Result is just data or different format
                            self.results_viewer.display_results(['Result'], [[str(result)]])
                    
                    self.status_label.configure(text="Query executed successfully")
                    
                    # Refresh sidebar if CREATE/ALTER/DROP operations were performed
                    query_upper = query.upper().strip()
                    if any(query_upper.startswith(cmd) for cmd in ["CREATE", "ALTER", "DROP"]):
                        if hasattr(self, 'sidebar') and self.sidebar:
                            try:
                                self.sidebar.refresh_all_panels()
                            except:
                                pass
                    
                    # Add to query history
                    if hasattr(self.db_manager, 'add_to_history'):
                        self.db_manager.add_to_history(query, "success")
                        # Force save to ensure it's persisted
                        if hasattr(self.db_manager, 'force_save_history'):
                            self.db_manager.force_save_history()
                        
                except Exception as e:
                    error_msg = f"Database Error: {str(e)}"
                    self.status_label.configure(text=error_msg)
                    # Show error in results viewer if available
                    if hasattr(self, 'results_viewer') and self.results_viewer:
                        self.results_viewer.display_error(error_msg)
                    # Add failed query to history
                    if hasattr(self.db_manager, 'add_to_history'):
                        self.db_manager.add_to_history(query, f"error: {str(e)}")
                        # Force save to ensure it's persisted
                        if hasattr(self.db_manager, 'force_save_history'):
                            self.db_manager.force_save_history()
            else:
                error_msg = "No database selected"
                self.status_label.configure(text=error_msg)
                # Show error in results viewer if available
                if hasattr(self, 'results_viewer') and self.results_viewer:
                    self.results_viewer.display_error(error_msg)
                
        except Exception as e:
            error_msg = f"Compilation Error: {str(e)}"
            self.status_label.configure(text=error_msg)
            # Show error in results viewer if available
            if hasattr(self, 'results_viewer') and self.results_viewer:
                self.results_viewer.display_error(error_msg)
            # Add failed query to history
            if hasattr(self.db_manager, 'add_to_history'):
                self.db_manager.add_to_history(query, f"compilation error: {str(e)}")
                # Force save to ensure it's persisted
                if hasattr(self.db_manager, 'force_save_history'):
                    self.db_manager.force_save_history()
    
    def clear_editor(self):
        """Clear the editor."""
        self.editor.delete("1.0", tk.END)
        self.status_label.configure(text="Editor cleared")
    
    def compile_sql(self):
        """Compile the SQL query and show the result."""
        query = self.editor.get("1.0", tk.END).strip()
        if not query:
            self.status_label.configure(text="No query to compile")
            return
        
        try:
            # Compile the SQL query
            compiled_query = self.sql_compiler.compile_sql(query)
            
            # Validate the compiled SQL
            validation_result = self.sql_compiler.validate_sql(compiled_query)
            
            if not validation_result['valid']:
                self.status_label.configure(text=f"Compilation Error: {', '.join(validation_result['errors'])}")
                # Show error in results viewer if available
                if hasattr(self, 'results_viewer') and self.results_viewer:
                    self.results_viewer.display_error(f"Compilation Error: {', '.join(validation_result['errors'])}")
                return
            
            # Show the compiled SQL in a new window
            self.show_compiled_sql(compiled_query, validation_result)
            
            # Also show compilation success in status
            self.status_label.configure(text="SQL compiled successfully")
            
        except Exception as e:
            error_msg = f"Compilation Error: {str(e)}"
            self.status_label.configure(text=error_msg)
            # Show error in results viewer if available
            if hasattr(self, 'results_viewer') and self.results_viewer:
                self.results_viewer.display_error(error_msg)
    
    def show_compiled_sql(self, compiled_sql, validation_result):
        """Show the compiled SQL in a popup window."""
        # Create popup window
        popup = tk.Toplevel(self.editor)
        popup.title("SQL Compiler Output")
        popup.geometry("900x700")
        popup.configure(bg="#1e1e1e")
        
        # Make popup modal
        popup.transient(self.editor)
        popup.grab_set()
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
        y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")
        
        # Header frame
        header_frame = tk.Frame(popup, bg="#1e1e1e")
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        title_label = tk.Label(header_frame, text="🔧 SQL Compiler Output", 
                              font=("Arial", 16, "bold"), fg="#ffffff", bg="#1e1e1e")
        title_label.pack(side=tk.LEFT)
        
        # Status label
        if validation_result['warnings']:
            status_text = f"⚠️ Warnings: {', '.join(validation_result['warnings'])}"
            status_color = "#ffa500"
        else:
            status_text = "✅ Compilation successful"
            status_color = "#00ff00"
        
        status_label = tk.Label(header_frame, text=status_text, 
                              font=("Arial", 12), fg=status_color, bg="#1e1e1e")
        status_label.pack(side=tk.RIGHT)
        
        # Create notebook for different views
        notebook = ttk.Notebook(popup)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Compiled SQL tab
        compiled_frame = ttk.Frame(notebook)
        notebook.add(compiled_frame, text="Compiled SQL")
        
        # Text area for compiled SQL
        text_frame = tk.Frame(compiled_frame, bg="#1e1e1e")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        text_widget = tk.Text(text_frame, 
                             font=("Consolas", 12),
                             bg="#2d2d2d", fg="#ffffff",
                             selectbackground="#404040", selectforeground="#ffffff",
                             relief="flat", bd=1, wrap=tk.WORD)
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Insert compiled SQL
        text_widget.insert("1.0", compiled_sql)
        text_widget.configure(state=tk.DISABLED)
        
        # Validation details tab
        validation_frame = ttk.Frame(notebook)
        notebook.add(validation_frame, text="Validation Details")
        
        validation_text = tk.Text(validation_frame, 
                                font=("Consolas", 11),
                                bg="#2d2d2d", fg="#ffffff",
                                selectbackground="#404040", selectforeground="#ffffff",
                                relief="flat", bd=1, wrap=tk.WORD)
        validation_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add validation details
        validation_details = f"Validation Status: {'Valid' if validation_result['valid'] else 'Invalid'}\n\n"
        if validation_result['errors']:
            validation_details += f"Errors:\n"
            for error in validation_result['errors']:
                validation_details += f"  ❌ {error}\n"
        if validation_result['warnings']:
            validation_details += f"\nWarnings:\n"
            for warning in validation_result['warnings']:
                validation_details += f"  ⚠️ {warning}\n"
        if not validation_result['errors'] and not validation_result['warnings']:
            validation_details += "No errors or warnings found.\n"
        
        validation_text.insert("1.0", validation_details)
        validation_text.configure(state=tk.DISABLED)
        
        # Button frame
        button_frame = tk.Frame(popup, bg="#1e1e1e")
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Copy button
        copy_btn = tk.Button(button_frame, text="📋 Copy to Editor", 
                            command=lambda: self.copy_compiled_sql(compiled_sql, popup),
                            bg="#007acc", fg="#ffffff", bd=0, font=("Arial", 10),
                            activebackground="#005a9e", activeforeground="#ffffff")
        copy_btn.pack(side=tk.LEFT, padx=5)
        
        # Run compiled SQL button with improved design
        run_btn = tk.Button(button_frame, text="▶ Run Compiled SQL", 
                           command=lambda: self.run_compiled_sql(compiled_sql, popup),
                           bg="#007acc", fg="#ffffff", bd=0, font=("Segoe UI", 11, "bold"),
                           activebackground="#005a9e", activeforeground="#ffffff",
                           relief="flat", padx=12, pady=6,
                           cursor="hand2")
        # Add hover effect
        def on_enter(e):
            run_btn.configure(bg="#0099ff")
        def on_leave(e):
            run_btn.configure(bg="#007acc")
        run_btn.bind("<Enter>", on_enter)
        run_btn.bind("<Leave>", on_leave)
        run_btn.pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_btn = tk.Button(button_frame, text="❌ Close", 
                             command=popup.destroy,
                             bg="#dc3545", fg="#ffffff", bd=0, font=("Arial", 10),
                             activebackground="#c82333", activeforeground="#ffffff")
        close_btn.pack(side=tk.RIGHT, padx=5)
    
    def copy_compiled_sql(self, compiled_sql, popup):
        """Copy the compiled SQL back to the editor."""
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", compiled_sql)
        popup.destroy()
        self.status_label.configure(text="Compiled SQL copied to editor")
    
    def run_compiled_sql(self, compiled_sql, popup):
        """Run the compiled SQL directly."""
        popup.destroy()
        
        # Replace current editor content with compiled SQL
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", compiled_sql)
        
        # Run the query
        self.run_query()
    
    def generate_sql(self):
        """Generate SQL using AI with database schema context."""
        if not self.ai_integration or not self.ai_integration.is_available():
            self.status_label.configure(text="AI integration not available")
            return
        
        # Get user prompt
        from tkinter import simpledialog
        user_prompt = simpledialog.askstring("AI SQL Generator", 
                                           "Describe what you want to do with the database:")
        
        if not user_prompt:
            return
        
        self.status_label.configure(text="Generating SQL with AI...")
        
        try:
            # Get database schema for AI context
            database_schema = {}
            if hasattr(self.db_manager, 'get_database_schema_for_ai'):
                database_schema = self.db_manager.get_database_schema_for_ai()
            
            # Generate SQL query using AI
            generated_sql = self.ai_integration.generate_sql_query(
                user_prompt=user_prompt,
                database_schema=database_schema,
                context=f"Current database: {self.db_manager.current_db or 'None'}"
            )
            
            if generated_sql:
                # Replace current editor content with generated SQL
                self.editor.delete("1.0", tk.END)
                self.editor.insert("1.0", generated_sql)
                self.status_label.configure(text="SQL generated successfully by AI")
            else:
                self.status_label.configure(text="Failed to generate SQL")
                
        except Exception as e:
            self.status_label.configure(text=f"AI Error: {str(e)}")
    
    def explain_sql(self):
        """Explain highlighted SQL or all SQL."""
        query, is_highlighted = self.get_query_for_ai()
        if not query:
            self.status_label.configure(text="No query to explain")
            return
        
        status_msg = "Explaining highlighted query..." if is_highlighted else "Explaining query..."
        self.status_label.configure(text=status_msg)
        
        if self.ai_integration:
            explanation = self.ai_integration.explain_sql(query)
            # Show explanation in a popup or status
            self.status_label.configure(text=f"Explanation: {explanation[:50]}...")
        else:
            self.status_label.configure(text="AI integration not available")
    
    def toggle_syntax(self):
        """Toggle syntax highlighting."""
        self.syntax_highlighting = not self.syntax_highlighting
        if self.syntax_highlighting:
            self.highlight_syntax()
            self.status_label.configure(text="Syntax highlighting enabled")
        else:
            self.status_label.configure(text="Syntax highlighting disabled")
    
    def toggle_minimap(self):
        """Toggle minimap visibility."""
        self.minimap_visible = not self.minimap_visible
        if self.minimap_visible:
            self.status_label.configure(text="Minimap enabled")
        else:
            self.status_label.configure(text="Minimap disabled")
    
    def toggle_ai_autocomplete(self):
        """Toggle AI autocomplete."""
        self.ai_autocomplete = not self.ai_autocomplete
        if self.ai_autocomplete:
            self.status_label.configure(text="AI autocomplete enabled")
        else:
            self.status_label.configure(text="AI autocomplete disabled")
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        from ui.components.improved_tooltip import create_improved_tooltip
        create_improved_tooltip(widget, text)
    
    def set_results_viewer(self, results_viewer):
        """Set reference to results viewer."""
        self.results_viewer = results_viewer
    
    def set_sidebar(self, sidebar):
        """Set reference to sidebar."""
        self.sidebar = sidebar
    
    def set_dashboard_panel(self, dashboard_panel):
        """Set reference to dashboard panel."""
        self.dashboard_panel = dashboard_panel
        # If we already have query results, set them in the dashboard
        if self.current_query_data:
            self.dashboard_panel.set_query_results(
                self.current_query,
                self.current_query_columns,
                self.current_query_data
            )
    
    def generate_dashboard(self):
        """Generate dashboard from current query results."""
        if not self.current_query_data or not self.current_query_columns:
            from tkinter import messagebox
            messagebox.showwarning("No Data", 
                                 "No query results available.\n\n"
                                 "Please run a SQL query first and then generate the dashboard.")
            return
        
        # Switch to dashboard tab if available
        if hasattr(self, 'dashboard_panel') and self.dashboard_panel:
            # Find the main window and switch to dashboard tab
            root = self.editor.winfo_toplevel()
            if hasattr(root, 'main_notebook'):
                # Find dashboard tab index
                tab_count = root.main_notebook.index("end")
                for i in range(tab_count):
                    tab_text = root.main_notebook.tab(i, "text")
                    if "Dashboard" in tab_text or "AI Dashboard" in tab_text:
                        root.main_notebook.select(i)
                        break
                # Generate dashboard
                self.dashboard_panel.generate_dashboard()
            else:
                self.dashboard_panel.generate_dashboard()
        else:
            from tkinter import messagebox
            messagebox.showwarning("Dashboard Not Available", 
                                 "Dashboard panel is not initialized.")
    
    def show_horizontal_ai_modal(self, initial_text=None):
        """Show the horizontal AI modal with highlighted query if available."""
        # Create horizontal AI modal if not exists
        if not self.horizontal_ai_modal:
            self.horizontal_ai_modal = HorizontalAIModal(
                self.parent,
                self.ai_integration,
                self,
                self.db_manager
            )
        
        # Get highlighted query or all query for AI prompt
        query, is_highlighted = self.get_query_for_ai()
        
        # If no initial text provided, use highlighted query or all query
        if initial_text is None and query:
            if is_highlighted:
                initial_text = f"Please help me with this highlighted query:\n\n{query}"
            else:
                initial_text = f"Please help me with this query:\n\n{query}"
        
        # Show modal at cursor position
        cursor_pos = self.editor.index(tk.INSERT)
        bbox = self.editor.bbox(cursor_pos)
        if bbox is not None:
            x, y, width, height = bbox
            # Convert to root coordinates
            root_x = self.editor.winfo_rootx() + x
            root_y = self.editor.winfo_rooty() + y + 20
            self.horizontal_ai_modal.show_at_position(root_x, root_y)
        else:
            # Fallback to center of editor
            center_x = self.editor.winfo_rootx() + self.editor.winfo_width() // 2
            center_y = self.editor.winfo_rooty() + self.editor.winfo_height() // 2
            self.horizontal_ai_modal.show_at_position(center_x, center_y)
        
        # Pre-fill input after modal is created (use after to ensure modal is ready)
        if initial_text:
            def prefill_input():
                try:
                    # Try using input_var first (StringVar)
                    if hasattr(self.horizontal_ai_modal, 'input_var') and self.horizontal_ai_modal.input_var:
                        self.horizontal_ai_modal.input_var.set(initial_text)
                    # Also try input_entry directly
                    elif hasattr(self.horizontal_ai_modal, 'input_entry') and self.horizontal_ai_modal.input_entry:
                        self.horizontal_ai_modal.input_entry.delete(0, tk.END)
                        self.horizontal_ai_modal.input_entry.insert(0, initial_text)
                        self.horizontal_ai_modal.input_entry.select_range(0, tk.END)
                except Exception as e:
                    print(f"Error pre-filling AI modal: {e}")
            
            # Wait a bit for modal to be ready, then pre-fill (try multiple times with increasing delay)
            self.editor.after(50, prefill_input)
            self.editor.after(150, prefill_input)  # Backup in case first one was too early
    
    def _handle_create_database(self, query: str):
        """Handle CREATE DATABASE command."""
        import re
        match = re.search(r'CREATE\s+DATABASE\s+(\w+)', query, re.IGNORECASE)
        if match:
            db_name = match.group(1)
            if hasattr(self.db_manager, 'create_database'):
                success = self.db_manager.create_database(db_name)
                if success:
                    self.status_label.configure(text=f"Database '{db_name}' created successfully")
                    if hasattr(self, 'results_viewer') and self.results_viewer:
                        self.results_viewer.display_results(['Message'], [[f"Database '{db_name}' created successfully"]])
                else:
                    self.status_label.configure(text=f"Failed to create database '{db_name}'")
                    if hasattr(self, 'results_viewer') and self.results_viewer:
                        self.results_viewer.display_error(f"Failed to create database '{db_name}'")
            else:
                self.status_label.configure(text="Database creation not supported")
        else:
            self.status_label.configure(text="Invalid CREATE DATABASE syntax")
    
    def _handle_use_database(self, query: str):
        """Handle USE DATABASE command."""
        import re
        match = re.search(r'USE\s+(\w+)', query, re.IGNORECASE)
        if match:
            db_name = match.group(1)
            if hasattr(self.db_manager, 'switch_database'):
                success = self.db_manager.switch_database(db_name)
                if success:
                    self.status_label.configure(text=f"Switched to database '{db_name}'")
                    if hasattr(self, 'results_viewer') and self.results_viewer:
                        self.results_viewer.display_results(['Message'], [[f"Switched to database '{db_name}'"]])
                else:
                    self.status_label.configure(text=f"Failed to switch to database '{db_name}'")
                    if hasattr(self, 'results_viewer') and self.results_viewer:
                        self.results_viewer.display_error(f"Failed to switch to database '{db_name}'")
            else:
                self.status_label.configure(text="Database switching not supported")
        else:
            self.status_label.configure(text="Invalid USE DATABASE syntax")
