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
        
        # Initialize SQL compiler
        self.sql_compiler = SimpleSQLCompiler()
        
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
        
        # Toolbar buttons
        self.create_toolbar_button(toolbar_frame, "▶️", "Run Query", self.run_query, "Run SQL (Ctrl+R)")
        self.create_toolbar_button(toolbar_frame, "🔧", "Compile", self.compile_sql, "Compile SQL (Ctrl+Shift+C)")
        self.create_toolbar_button(toolbar_frame, "🧹", "Clear", self.clear_editor, "Clear Editor (Ctrl+C)")
        self.create_toolbar_button(toolbar_frame, "🤖", "AI Generate", self.generate_sql, "AI Generate (Ctrl+G)")
        self.create_toolbar_button(toolbar_frame, "💡", "Explain", self.explain_sql, "Explain SQL")
        
        # Separator
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Editor options
        self.create_toolbar_button(toolbar_frame, "🎨", "Syntax", self.toggle_syntax, "Toggle Syntax Highlighting")
        self.create_toolbar_button(toolbar_frame, "🗺️", "Minimap", self.toggle_minimap, "Toggle Minimap")
        self.create_toolbar_button(toolbar_frame, "🤖", "AI Auto", self.toggle_ai_autocomplete, "Toggle AI Autocomplete")
        
        # Separator
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Line numbers
        self.line_numbers = tk.Text(toolbar_frame, width=4, height=1, 
                                   bg="#1e1e1e", fg="#888888", 
                                   font=("Consolas", 11), state=tk.DISABLED,
                                   relief="flat", bd=0)
        self.line_numbers.pack(side=tk.RIGHT, padx=5)
        
    def create_toolbar_button(self, parent, emoji, tooltip, command, full_tooltip):
        """Create a toolbar button."""
        btn = tk.Button(parent, text=emoji, command=command,
                       bg="#2d2d2d", fg="#ffffff", bd=0,
                       font=("Arial", 10), width=3, height=1,
                       activebackground="#404040", activeforeground="#ffffff")
        btn.pack(side=tk.LEFT, padx=2)
        
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
    
    def on_click(self, event):
        """Handle click event."""
        self.update_cursor_position()
    
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
        context_menu.add_separator()
        
        # AI operations
        context_menu.add_command(label="🤖 AI Generate", command=self.ai_generate_popup)
        context_menu.add_command(label="💡 AI Explain", command=self.ai_explain)
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
    
    def ai_generate_popup(self):
        """Show AI generate popup."""
        from ui.components.ai_popup import AIPopup
        ai_popup = AIPopup(self.editor, self.ai_integration, self, self.db_manager)
        # Create a fake event for the popup
        fake_event = type('Event', (), {'x_root': self.editor.winfo_rootx() + 100, 'y_root': self.editor.winfo_rooty() + 100})()
        ai_popup.show_popup(fake_event)
    
    def ai_explain(self):
        """Explain selected SQL."""
        try:
            selected_text = self.editor.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                if self.ai_integration:
                    explanation = self.ai_integration.explain_sql(selected_text)
                    # Show explanation in a popup
                    from tkinter import messagebox
                    messagebox.showinfo("AI Explanation", explanation)
                else:
                    self.status_label.configure(text="AI integration not available")
            else:
                self.status_label.configure(text="Please select SQL text to explain")
        except:
            self.status_label.configure(text="Please select SQL text to explain")
    
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
                self.status_label.configure(text=f"SQL Error: {', '.join(validation_result['errors'])}")
                return
            
            # Show warnings if any
            if validation_result['warnings']:
                self.status_label.configure(text=f"Warnings: {', '.join(validation_result['warnings'])}")
            
            # Execute the compiled query through the database manager
            if self.db_manager and self.db_manager.current_db:
                try:
                    # Execute the query
                    result = self.db_manager.execute_query(compiled_query)
                    
                    # Display results in the results viewer
                    if hasattr(self, 'results_viewer') and self.results_viewer:
                        self.results_viewer.display_results(result)
                    
                    self.status_label.configure(text="Query executed successfully")
                    
                    # Add to query history
                    if hasattr(self.db_manager, 'add_to_history'):
                        self.db_manager.add_to_history(query)
                        
                except Exception as e:
                    self.status_label.configure(text=f"Database Error: {str(e)}")
            else:
                self.status_label.configure(text="No database selected")
                
        except Exception as e:
            self.status_label.configure(text=f"Compilation Error: {str(e)}")
    
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
                return
            
            # Show the compiled SQL in a new window
            self.show_compiled_sql(compiled_query, validation_result)
            
        except Exception as e:
            self.status_label.configure(text=f"Compilation Error: {str(e)}")
    
    def show_compiled_sql(self, compiled_sql, validation_result):
        """Show the compiled SQL in a popup window."""
        # Create popup window
        popup = tk.Toplevel(self.editor)
        popup.title("Compiled SQL")
        popup.geometry("800x600")
        popup.configure(bg="#1e1e1e")
        
        # Header frame
        header_frame = tk.Frame(popup, bg="#1e1e1e")
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        title_label = tk.Label(header_frame, text="🔧 Compiled SQL Query", 
                              font=("Arial", 14, "bold"), fg="#ffffff", bg="#1e1e1e")
        title_label.pack(side=tk.LEFT)
        
        # Status label
        if validation_result['warnings']:
            status_text = f"⚠️ Warnings: {', '.join(validation_result['warnings'])}"
            status_color = "#ffa500"
        else:
            status_text = "✅ Compilation successful"
            status_color = "#00ff00"
        
        status_label = tk.Label(header_frame, text=status_text, 
                              font=("Arial", 10), fg=status_color, bg="#1e1e1e")
        status_label.pack(side=tk.RIGHT)
        
        # Text area for compiled SQL
        text_frame = tk.Frame(popup, bg="#1e1e1e")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        text_widget = tk.Text(text_frame, 
                             font=("Consolas", 11),
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
        
        # Button frame
        button_frame = tk.Frame(popup, bg="#1e1e1e")
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Copy button
        copy_btn = tk.Button(button_frame, text="📋 Copy to Editor", 
                            command=lambda: self.copy_compiled_sql(compiled_sql, popup),
                            bg="#007acc", fg="#ffffff", bd=0, font=("Arial", 10),
                            activebackground="#005a9e", activeforeground="#ffffff")
        copy_btn.pack(side=tk.LEFT, padx=5)
        
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
        """Explain the current SQL query."""
        query = self.editor.get("1.0", tk.END).strip()
        if not query:
            self.status_label.configure(text="No query to explain")
            return
        
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
