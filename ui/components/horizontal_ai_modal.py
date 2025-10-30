"""
Horizontal AI Query Assistant Modal - A compact, tooltip-style modal for AI query assistance
"""

import tkinter as tk
import ttkbootstrap as ttk
from typing import Optional, List, Dict, Any
import sys
import os
import re
import time

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ui.components.modern_theme import ModernTheme
from ai.ai_pipeline import AIPipeline


class HorizontalAIModal:
    """
    A compact, horizontal tooltip-style AI modal that appears on demand.
    Features:
    - Inline chat interface like Cursor's AI assistant
    - Code suggestions with Keep/Discard buttons
    - Visual highlighting for old code (red) and applied code (green)
    - Smooth UI transitions with fade/slide animations
    - No popup confirmations - all actions inline
    - Table/column selection with @ and # triggers
    """
    
    def __init__(self, parent, ai_integration, sql_editor, db_manager):
        self.parent = parent
        self.ai_integration = ai_integration
        self.sql_editor = sql_editor
        self.db_manager = db_manager
        self.theme = ModernTheme()
        
        # Modal state
        self.modal_window = None
        self.is_visible = False
        self.conversation_history = []
        self.selected_tables = []
        self.selected_columns = {}
        
        # UI components
        self.input_entry = None
        self.history_frame = None
        self.chat_frame = None
        self.chat_text = None
        self.chat_scrollbar = None
        self.chat_messages = []
        self.table_dropdown = None
        self.column_dropdown = None
        self.dropdown_window = None
        self.current_dropdown_type = None
        self.suggestion_buttons = {}  # Track active suggestion buttons
        self.inline_buttons = {}  # Track inline suggestion buttons
        
        # Configuration
        self.modal_width = 800
        self.modal_height = 120
        self.chat_height = 150
        self.auto_hide_delay = 10000  # 10 seconds
        self.chat_expanded = False
        
        # Runtime flags/state
        self.warning_active = False
        
        # Selection mode state
        self.selection_text = None
        self.selection_mode = False
        self.selection_mode_label = None
        
        # Auto-resize thresholds
        self._max_chat_extra_px = 360  # maximum additional height for chat area
        self._base_modal_height = self.modal_height
        self._min_chat_extra_px = 36   # minimal visible chat height for very short messages
        
        # Lightweight in-memory session context (rolling)
        self.session_context = []  # list of {'role': 'user'|'assistant', 'content': str}
        self._max_context_items = 10
        
        # Per-trigger AI response guard to avoid duplicate assistant blocks
        self.ai_response_pending = False
        
    def show_modal(self, event=None, position=None):
        """Show the horizontal AI modal with smart positioning and selection mode detection."""
        if self.is_visible:
            self.hide_modal()
            return
        self.is_visible = True

        # Detect SQL selection
        self.selection_text = None
        self.selection_mode = False
        try:
            sel = self.get_selected_text_from_editor()
            if sel and self._is_valid_sql_selection(sel):
                self.selection_text = sel
                self.selection_mode = True
            else:
                self.selection_mode = False # fallback
        except Exception as e:
            print(f"Selection check error: {e}")
            self.selection_mode = False
            
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
        
        # Focus modal but do not grab, so editor selection still works
        self.modal_window.focus_force()
        
        # Create main frame with subtle shadow effect
        main_frame = tk.Frame(self.modal_window, bg="#2d2d2d", relief="raised", bd=1)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Create content frame
        content_frame = tk.Frame(main_frame, bg="#2d2d2d")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        
        # Create the horizontal layout
        self.create_horizontal_layout(content_frame)
        
        # Create chat interface
        self.create_chat_interface(content_frame)
        
        # Bind events
        self.bind_events()
        # Enable dragging and clamp within app window
        try:
            self._enable_drag_on(self.modal_window)
            self.parent.bind("<Configure>", lambda e: self._on_parent_resize_or_state(e), add='+')
        except Exception:
            pass
        
        # Bind click events to SQL editor to remove highlights
        if hasattr(self.sql_editor, 'editor'):
            self.sql_editor.editor.bind("<Button-1>", self.on_editor_click)
            self.sql_editor.editor.bind("<Key>", self.on_editor_key)
            # Support dropping orange prompt highlight
            try:
                self.sql_editor.editor.bind("<Double-1>", self.on_editor_double_click, add='+')
                self.sql_editor.editor.bind("<ButtonRelease-1>", self.on_editor_selection_release, add='+')
            except Exception:
                pass
        
        # Focus and select text
        self.input_entry.focus()
        self.input_entry.select_range(0, tk.END)
        
        # At the end, add the selection mode label if active
        if self.selection_mode and hasattr(self, 'chat_frame'):
            self._show_selection_mode_label(self.chat_frame)
        
    def create_horizontal_layout(self, parent):
        """Create the horizontal layout for the modal."""
        # Top row - Input and controls
        top_frame = tk.Frame(parent, bg="#2d2d2d")
        top_frame.pack(fill=tk.X, pady=(0, 5))
        
        # AI icon
        ai_icon = tk.Label(top_frame, text="🤖", font=("Arial", 12), 
                          bg="#2d2d2d", fg="#ffffff")
        ai_icon.pack(side=tk.LEFT, padx=(0, 8))
        
        # Input entry with @ and # support
        self.input_var = tk.StringVar()
        self.input_var.trace('w', self.on_text_change)
        self.input_entry = tk.Entry(top_frame, 
                                   textvariable=self.input_var,
                                   font=("Consolas", 10),
                                   bg="#404040", fg="#ffffff",
                                   insertbackground="#ffffff",
                                   relief="flat", bd=0,
                                   width=60)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        # Action buttons
        button_frame = tk.Frame(top_frame, bg="#2d2d2d")
        button_frame.pack(side=tk.RIGHT)
        
        # Generate/Send button
        generate_btn = tk.Button(button_frame, text="▶", 
                               command=self.generate_sql,
                               bg="#007acc", fg="#ffffff", bd=0,
                               font=("Arial", 9, "bold"), 
                               width=3, height=1,
                               activebackground="#005a9e", 
                               activeforeground="#ffffff",
                               relief="flat")
        generate_btn.pack(side=tk.LEFT, padx=(0, 3))
        
        # Close button
        close_btn = tk.Button(button_frame, text="✕", 
                            command=self.hide_modal,
                            bg="#dc3545", fg="#ffffff", bd=0,
                            font=("Arial", 9, "bold"), 
                            width=3, height=1,
                            activebackground="#c82333", 
                            activeforeground="#ffffff",
                            relief="flat")
        close_btn.pack(side=tk.LEFT)
        
    def create_chat_interface(self, parent):
        """Create the chat interface with ScrolledText for inline messages."""
        # Chat frame (initially hidden)
        self.chat_frame = tk.Frame(parent, bg="#2d2d2d", height=0)
        # Will be shown when chat_expanded is True
        
        # Create ScrolledText for chat display
        chat_container = tk.Frame(self.chat_frame, bg="#2d2d2d")
        chat_container.pack(fill=tk.BOTH, expand=True, padx=4, pady=3)
        
        # Scrollbar
        self.chat_scrollbar = tk.Scrollbar(chat_container)
        self.chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Text widget with rich text support
        self.chat_text = tk.Text(chat_container, 
                                 bg="#1e1e1e", 
                                 fg="#ffffff",
                                 font=("Consolas", 9),
                                 wrap=tk.WORD,
                                 yscrollcommand=self.chat_scrollbar.set,
                                 highlightthickness=0,
                                 relief="flat",
                                 bd=0)
        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=0, pady=0)
        self.chat_scrollbar.config(command=self.chat_text.yview)
        
        # Configure text tags for styling
        self.configure_chat_tags()
        
        # Button tracking for inline suggestions
        self.inline_buttons = {}
        
    def configure_chat_tags(self):
        """Configure text tags for chat styling."""
        # Role tags
        self.chat_text.tag_configure("user_role", 
                                     foreground="#007acc", 
                                     font=("Arial", 9, "bold"),
                                     spacing1=1, spacing2=1, spacing3=2)
        self.chat_text.tag_configure("ai_role", 
                                     foreground="#28a745", 
                                     font=("Arial", 9, "bold"),
                                     spacing1=1, spacing2=1, spacing3=2)
        
        # Content tags
        self.chat_text.tag_configure("normal_text", 
                                     foreground="#ffffff", 
                                     font=("Consolas", 9),
                                     spacing1=1, spacing2=1, spacing3=2)
        
        # Old code styling (red, italic) - compact margins
        self.chat_text.tag_configure("old_code", 
                                     foreground="#ff6b6b",
                                     background="#4d0000",
                                     font=("Consolas", 9, "italic"),
                                     lmargin1=6, lmargin2=6,
                                     spacing1=1, spacing2=1, spacing3=2)
        
        # New code styling (green) - compact margins
        self.chat_text.tag_configure("new_code", 
                                     foreground="#90EE90",
                                     font=("Consolas", 9),
                                     lmargin1=6, lmargin2=6,
                                     spacing1=1, spacing2=1, spacing3=2)
        
        # AI suggestion label - subtle separation
        self.chat_text.tag_configure("ai_suggestion_label", 
                                     foreground="#17a2b8",
                                     font=("Arial", 9, "bold"),
                                     lmargin1=2, lmargin2=2,
                                     spacing1=1, spacing2=1, spacing3=2)
        
        # Separator line - minimal spacing
        self.chat_text.tag_configure("separator", 
                                     foreground="#444444",
                                     spacing1=1, spacing2=1, spacing3=2)
        
    def add_chat_message(self, role, content, suggestion_data=None):
        """Add a message to the chat interface using ScrolledText with inline buttons."""
        if not self.chat_expanded:
            self.expand_chat()
        
        # Ensure chat_text exists
        if not hasattr(self, 'chat_text'):
            return
        
        # Role indicator
        role_emoji = "👤" if role == "user" else "🤖"
        role_tag = "user_role" if role == "user" else "ai_role"
        
        # Insert role header
        self.chat_text.insert(tk.END, f"{role_emoji} {role.upper()}: ", role_tag)
        
        # Insert content
        self.chat_text.insert(tk.END, f"{content}\n", "normal_text")
        
        # Record in rolling session context
        try:
            self.session_context.append({'role': role, 'content': content})
            if len(self.session_context) > self._max_context_items:
                self.session_context = self.session_context[-self._max_context_items:]
        except Exception:
            pass
        
        # Add suggestion with inline buttons if provided
        if suggestion_data:
            self.add_code_suggestion_inline(suggestion_data)
        
        # Scroll to bottom and auto-resize (visual only)
        self.chat_text.see(tk.END)
        self._auto_resize_chat()
        self._resize_to_content()
    
    def _compute_gapped_text(self, insert_pos: str, new_code: str) -> str:
        """Return new_code wrapped so there is exactly one blank line before and after it."""
        try:
            editor = self.sql_editor.editor
            body = (new_code or "").strip("\n")
            # Determine prefix
            try:
                prev_two = editor.get(f"{insert_pos}-2c", insert_pos)
            except Exception:
                prev_two = ""
            if prev_two.endswith("\n\n"):
                prefix = ""
            elif prev_two.endswith("\n"):
                prefix = "\n"
            else:
                prefix = "\n\n"
            # Determine suffix
            try:
                next_two = editor.get(insert_pos, f"{insert_pos}+2c")
            except Exception:
                next_two = ""
            if next_two.startswith("\n\n"):
                suffix = ""
            elif next_two.startswith("\n"):
                suffix = "\n"
            else:
                suffix = "\n\n"
            return prefix + body + suffix
        except Exception:
            return "\n\n" + (new_code or "").strip("\n") + "\n\n"
        
        # Store message info for tracking
        self.chat_messages.append({
            'role': role,
            'content': content,
            'suggestion_data': suggestion_data
        })
        
        # Add smooth fade-in effect
        self.animate_message_fade()
        
        # If assistant returned SQL, show compact Keep/Reject actions
        try:
            if role == "assistant":
                if suggestion_data and suggestion_data.get('new_code'):
                    # Suggestion already rendered; nothing else needed
                    pass
                elif self._looks_like_sql(content or ""):
                    # Render compact suggestion for plain SQL answer
                    try:
                        self._add_suggestion_block("", content)
                    except Exception:
                        pass
        except Exception:
            pass
    
    def add_code_suggestion_inline(self, suggestion_data):
        """Add code suggestion inline with Keep/Discard buttons using window_create."""
        # Highlight old code in editor (red) if replacing existing code
        if suggestion_data.get('old_start') and suggestion_data.get('old_end'):
            self.highlight_old_code(suggestion_data['old_start'], suggestion_data['old_end'])
        
        # Add separator line
        self.chat_text.insert(tk.END, "─" * 60 + "\n", "separator")
        
        # Add AI Suggestion label
        self.chat_text.insert(tk.END, "💡 AI Suggestion:\n", "ai_suggestion_label")
        
        # Add old code (if exists) - only show if there's existing code to replace
        if suggestion_data.get('old_code') and suggestion_data['old_code']:
            old_code = suggestion_data['old_code']
            if len(old_code) > 100:
                old_code = old_code[:100] + "..."
            self.chat_text.insert(tk.END, f"OLD: ", "ai_suggestion_label")
            self.chat_text.insert(tk.END, f"{old_code}\n", "old_code")
        
        # Add new code - this should always exist
        if suggestion_data.get('new_code'):
            new_code = suggestion_data['new_code']
            # Always show NEW label even if no OLD
            self.chat_text.insert(tk.END, f"NEW: ", "ai_suggestion_label")
            self.chat_text.insert(tk.END, f"{new_code}\n", "new_code")
        
        # Tight spacer before buttons
        self.chat_text.insert(tk.END, "\n", "normal_text")
        
        # Create compact text-like buttons (no box background)
        keep_btn = tk.Button(self.chat_text,
                            text="Keep",
                            bg="#1e1e1e", fg="#17a2b8", bd=0,
                            font=("Arial", 9, "underline"),
                            cursor="hand2",
                            relief="flat", activebackground="#1e1e1e",
                            activeforeground="#1fbad1", highlightthickness=0)
        discard_btn = tk.Button(self.chat_text,
                              text="Reject",
                              bg="#1e1e1e", fg="#bbbbbb", bd=0,
                              font=("Arial", 9, "underline"),
                              cursor="hand2",
                              relief="flat", activebackground="#1e1e1e",
                              activeforeground="#cccccc", highlightthickness=0)
        
        # Hover cursor and soft hover effects (safe, visual-only)
        try:
            keep_btn.configure(cursor="hand2")
            discard_btn.configure(cursor="hand2")
            # Soft hover tint
            keep_btn.bind("<Enter>", lambda e, b=keep_btn: b.configure(bg="#2ecc71"))
            keep_btn.bind("<Leave>", lambda e, b=keep_btn: b.configure(bg="#28a745"))
            discard_btn.bind("<Enter>", lambda e, b=discard_btn: b.configure(bg="#e35d6a"))
            discard_btn.bind("<Leave>", lambda e, b=discard_btn: b.configure(bg="#dc3545"))
        except Exception:
            pass
        
        # Insert buttons inline using window_create (compact spacing)
        keep_btn_ref = keep_btn
        discard_btn_ref = discard_btn
        # Now that refs exist, bind commands
        keep_btn_ref.configure(command=lambda s=suggestion_data, kb=keep_btn_ref, rb=discard_btn_ref: self._compact_keep_action(s, kb, rb))
        discard_btn_ref.configure(command=lambda s=suggestion_data, kb=keep_btn_ref, rb=discard_btn_ref: self._compact_reject_action(s, kb, rb))

        self.chat_text.window_create(tk.END, window=keep_btn_ref)
        self.chat_text.insert(tk.END, "    ")
        self.chat_text.window_create(tk.END, window=discard_btn_ref)
        self.chat_text.insert(tk.END, "\n", "normal_text")
        
        # Store button references for tracking
        suggestion_id = f"suggestion_{len(self.chat_messages)}"
        self.inline_buttons[suggestion_id] = {
            'keep': keep_btn_ref,
            'discard': discard_btn_ref,
            'data': suggestion_data
        }
        
        # Auto-resize after adding suggestion (visual only)
        self._auto_resize_chat()
        self._resize_to_content()
    
    def handle_keep_suggestion(self, suggestion_data):
        """Handle Keep button click - apply suggestion to editor."""
        try:
            if suggestion_data.get('old_start') and suggestion_data.get('old_end'):
                # Replace existing code
                old_start = suggestion_data['old_start']
                old_end = suggestion_data['old_end']
                self.sql_editor.editor.delete(old_start, old_end)
                text = self._compute_gapped_text(old_start, suggestion_data['new_code'])
                self.sql_editor.editor.insert(old_start, text)
                
                # Highlight applied code in green
                new_end = self.sql_editor.editor.index(f"{old_start}+{len(text)}c")
                self.highlight_applied_code(old_start, new_end)
                # Tag for undo
                try:
                    self.sql_editor.editor.tag_remove("ai_last_insert", "1.0", tk.END)
                except Exception:
                    pass
                self.sql_editor.editor.tag_add("ai_last_insert", old_start, new_end)
                self._last_ai_insert_range = (old_start, new_end)
            else:
                # Insert at cursor
                cursor_pos = self.sql_editor.editor.index(tk.INSERT)
                text = self._compute_gapped_text(cursor_pos, suggestion_data['new_code'])
                self.sql_editor.editor.insert(cursor_pos, text)
                
                # Highlight applied code
                new_end = self.sql_editor.editor.index(f"{cursor_pos}+{len(text)}c")
                self.highlight_applied_code(cursor_pos, new_end)
                # Tag for undo
                try:
                    self.sql_editor.editor.tag_remove("ai_last_insert", "1.0", tk.END)
                except Exception:
                    pass
                self.sql_editor.editor.tag_add("ai_last_insert", cursor_pos, new_end)
                self._last_ai_insert_range = (cursor_pos, new_end)
            
            # Add confirmation message to chat
            self.add_confirmation_message("✅ Query inserted")
            
            # Disable buttons
            self.disable_suggestion_buttons(suggestion_data)
            
        except Exception as e:
            print(f"Error applying suggestion: {e}")
            self.add_confirmation_message(f"❌ Error applying suggestion: {str(e)}")

    def _compact_keep_action(self, suggestion_data, keep_btn_ref, discard_btn_ref):
        try:
            self.handle_keep_suggestion(suggestion_data)
            try:
                keep_btn_ref.config(text="Query inserted", state=tk.DISABLED, fg="#28a745", font=("Arial", 9))
                discard_btn_ref.config(state=tk.DISABLED)
            except Exception:
                pass
        except Exception:
            pass

    def _compact_reject_action(self, suggestion_data, keep_btn_ref, discard_btn_ref):
        try:
            self.handle_discard_suggestion(suggestion_data)
            try:
                discard_btn_ref.config(text="Query rejected", state=tk.DISABLED, fg="#dc3545", font=("Arial", 9))
                keep_btn_ref.config(state=tk.DISABLED)
            except Exception:
                pass
        except Exception:
            pass

    # Removed inline Insert/Undo bar per new compact UX
    
    def handle_discard_suggestion(self, suggestion_data):
        """Handle Discard button click - ignore suggestion."""
        # Remove any highlights from old code
        if suggestion_data.get('old_start') and suggestion_data.get('old_end'):
            self.remove_old_highlight(suggestion_data['old_start'], suggestion_data['old_end'])
        
        # Add discard message to chat
        self.add_confirmation_message("❌ Query rejected")
        
        # Disable buttons
        self.disable_suggestion_buttons(suggestion_data)
    
    def disable_suggestion_buttons(self, suggestion_data):
        """Disable the Keep/Discard buttons after action."""
        try:
            for btn_id, btn_info in self.inline_buttons.items():
                if btn_info['data'] == suggestion_data:
                    btn_info['keep'].config(state=tk.DISABLED)
                    btn_info['discard'].config(state=tk.DISABLED)
                    break
        except Exception as e:
            print(f"Error disabling buttons: {e}")
    
    def add_confirmation_message(self, message):
        """Add a confirmation message to chat."""
        self.chat_text.insert(tk.END, f"{message}\n\n", "separator")
        self.chat_text.see(tk.END)
    
    def animate_message_fade(self):
        """Animate fade-in effect for new messages."""
        try:
            # Simple implementation using after
            self.modal_window.after(50, lambda: self.modal_window.update())
        except:
            pass
    
    def expand_chat(self):
        """Expand chat interface with animation."""
        if self.chat_expanded:
            return
        
        self.chat_expanded = True
        
        # Pack chat frame
        self.chat_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Resize modal
        new_height = self.modal_height + self.chat_height
        self.modal_window.wm_geometry(f"{self.modal_width}x{new_height}")
        
        # Animate alpha transition
        for alpha in range(950, 1001, 10):
            self.modal_window.wm_attributes("-alpha", alpha / 1000)
            self.modal_window.update()
            time.sleep(0.01)
    
    def highlight_old_code(self, start_pos, end_pos):
        """Highlight old code in red."""
        try:
            self.sql_editor.editor.tag_configure("ai_old", 
                                                background="#4d0000",
                                                foreground="#ffcccc",
                                                relief="raised",
                                                borderwidth=1)
            self.sql_editor.editor.tag_add("ai_old", start_pos, end_pos)
        except Exception as e:
            print(f"Error highlighting old code: {e}")
    
    def highlight_applied_code(self, start_pos, end_pos):
        """Highlight applied code in green."""
        try:
            self.sql_editor.editor.tag_configure("ai_applied", 
                                                background="#004d00",
                                                foreground="#ccffcc",
                                                relief="raised",
                                                borderwidth=1)
            self.sql_editor.editor.tag_add("ai_applied", start_pos, end_pos)
            
            # Auto-remove after 3 seconds
            self.modal_window.after(3000, lambda: self.remove_highlight("ai_applied"))
        except Exception as e:
            print(f"Error highlighting applied code: {e}")
    
    def remove_old_highlight(self, start_pos, end_pos):
        """Remove old code highlight."""
        try:
            self.sql_editor.editor.tag_remove("ai_old", start_pos, end_pos)
        except Exception as e:
            print(f"Error removing old highlight: {e}")
        
        
    def create_history_content(self):
        """Create the conversation history content."""
        if not self.history_frame:
            return
            
        # History header
        history_header = tk.Frame(self.history_frame, bg="#2d2d2d")
        history_header.pack(fill=tk.X, pady=(0, 5))
        
        history_title = tk.Label(history_header, text="💬 Conversation History", 
                               font=("Arial", 9, "bold"), fg="#ffffff", bg="#2d2d2d")
        history_title.pack(side=tk.LEFT)
        
        clear_btn = tk.Button(history_header, text="🗑️ Clear", 
                            command=self.clear_history,
                            bg="#666666", fg="#ffffff", bd=0,
                            font=("Arial", 8), 
                            width=6, height=1,
                            activebackground="#888888", 
                            activeforeground="#ffffff",
                            relief="flat")
        clear_btn.pack(side=tk.RIGHT)
        
        # History scrollable area
        history_container = tk.Frame(self.history_frame, bg="#2d2d2d")
        history_container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        history_scrollbar = ttk.Scrollbar(history_container)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # History text widget
        self.history_text = tk.Text(history_container, 
                                   height=8, wrap=tk.WORD,
                                   font=("Consolas", 9), 
                                   bg="#1e1e1e", fg="#ffffff",
                                   relief="flat", bd=1, state=tk.DISABLED,
                                   yscrollcommand=history_scrollbar.set)
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.config(command=self.history_text.yview)
        
    def bind_events(self):
        """Bind events for the modal."""
        # Input entry events
        self.input_entry.bind("<Return>", lambda e: self.generate_sql())
        self.input_entry.bind("<Escape>", lambda e: self.hide_modal())
        self.input_entry.bind("<KeyPress>", self.on_key_press)
        self.input_entry.bind("<KeyRelease>", self.on_key_release)
        self.input_entry.bind("<FocusIn>", self.on_focus_in)
        self.input_entry.bind("<FocusOut>", self.on_focus_out)
        
        # Modal events
        self.modal_window.bind("<FocusOut>", self.on_modal_focus_out)
        self.modal_window.bind("<Button-1>", self.on_modal_click)
        # Hide dropdowns on space anywhere in the modal
        try:
            self.modal_window.bind("<space>", lambda e: self.hide_dropdown())
            self.modal_window.bind("<KeyPress-space>", lambda e: self.hide_dropdown())
        except Exception:
            pass
        # Keyboard shortcuts: Ctrl+? or Ctrl+/ to send; press again to undo last AI insertion
        try:
            sequences = (
                "<Control-question>",
                "<Control-slash>",
                "<Control-Shift-slash>",
                "<Control-Key-/>",
                "<Control-Shift-Key-/>",
                "<Control-Key-KP_Divide>",
            )
            for seq in sequences:
                self.modal_window.bind(seq, self._handle_ctrl_question, add='+')
                if self.input_entry:
                    self.input_entry.bind(seq, self._handle_ctrl_question, add='+')
                if hasattr(self.sql_editor, 'editor'):
                    self.sql_editor.editor.bind(seq, self._handle_ctrl_question, add='+')
                self.parent.bind(seq, self._handle_ctrl_question, add='+')
            # Global capture to ensure default behavior is suppressed
            try:
                self.parent.bind_all("<Control-slash>", self._handle_ctrl_question, add='+')
                self.parent.bind_all("<Control-Shift-slash>", self._handle_ctrl_question, add='+')
                self.parent.bind_all("<Control-Key-/>", self._handle_ctrl_question, add='+')
                self.parent.bind_all("<Control-Shift-Key-/>", self._handle_ctrl_question, add='+')
                self.parent.bind_all("<Control-question>", self._handle_ctrl_question, add='+')
            except Exception:
                pass
        except Exception:
            pass
        
    def on_key_press(self, event):
        """Handle key press events for @ and # triggers."""
        char = event.char
        keysym = event.keysym
        print(f"Key pressed: char='{char}', keysym='{keysym}'")  # Debug print
        
        if char == '@' or keysym == 'at':
            # Show table dropdown
            print("Showing table dropdown")  # Debug print
            self.show_table_dropdown()
            return "break"
        elif char == '#' or keysym == 'numbersign':
            # Show column dropdown
            print("Showing column dropdown")  # Debug print
            self.show_column_dropdown()
            return "break"
        elif char == ' ' or keysym == 'space':
            # Hide dropdowns on space
            self.hide_dropdown()
        
        # Allow normal typing
        return
    
    def on_key_release(self, event):
        """Handle key release events."""
        char = event.char
        keysym = event.keysym
        print(f"Key released: char='{char}', keysym='{keysym}'")  # Debug print
        
        # Check for @ and # on key release as well
        if char == '@' or keysym == 'at':
            print("Key release: @ detected")
        elif char == '#' or keysym == 'numbersign':
            print("Key release: # detected")
        elif char == ' ' or keysym == 'space':
            # Also hide dropdowns on space key release
            try:
                self.hide_dropdown()
            except Exception:
                pass
    
    def on_text_change(self, *args):
        """Handle text changes in the input field."""
        current_text = self.input_var.get()
        print(f"Text changed: '{current_text}'")  # Debug print
        
        # Check if the last character is @ or #
        if current_text.endswith('@'):
            print("Text change: @ detected at end")
            # Small delay to prevent modal from closing
            self.modal_window.after(100, self.show_table_dropdown)
        elif current_text.endswith('#'):
            print("Text change: # detected at end")
            # Small delay to prevent modal from closing
            self.modal_window.after(100, self.show_column_dropdown)
            
    def on_focus_in(self, event):
        """Handle focus in event."""
        pass
        
    def on_focus_out(self, event):
        """Handle focus out event."""
        pass
        
    def on_modal_focus_out(self, event):
        """Handle modal focus out event."""
        # Don't auto-hide on focus out to prevent modal from disappearing
        # User can close with Escape key or close button
        pass
            
    def on_modal_click(self, event):
        """Handle click on modal to prevent auto-hide."""
        pass

    def _debug_print_prompt(self, prompt_text: str):
        try:
            print("\n===== AI PROMPT (BEGIN) =====")
            print(prompt_text)
            print("===== AI PROMPT (END) =====\n")
        except Exception as e:
            try:
                print(f"[AI PROMPT DEBUG ERROR]: {e}")
            except Exception:
                pass

    def _handle_ctrl_question(self, event=None):
        try:
            # Always prevent default behavior for this shortcut
            result_break = "break"
            # If there is a last AI insertion and no selection and input empty -> undo
            has_sel = False
            try:
                has_sel = bool(self.sql_editor.editor.tag_ranges(tk.SEL))
            except Exception:
                has_sel = False
            try:
                input_empty = not bool((self.input_var.get() or '').strip())
            except Exception:
                input_empty = True
            if getattr(self, '_last_ai_insert_range', None) and (not has_sel) and input_empty:
                self._undo_last_ai_insertion()
                return result_break
            # Otherwise send/generate
            self.generate_sql()
            return result_break
        except Exception:
            try:
                self.generate_sql()
            except Exception:
                pass
            return "break"

    def _undo_last_ai_insertion(self):
        try:
            rng = getattr(self, '_last_ai_insert_range', None)
            if not rng:
                self.add_confirmation_message("ℹ️ Nothing to undo")
                return
            start_idx, end_idx = rng
            # Remove content if range still valid
            try:
                self.sql_editor.editor.delete(start_idx, end_idx)
            except Exception:
                pass
            # Remove tag and clear marker
            try:
                self.sql_editor.editor.tag_remove("ai_last_insert", "1.0", tk.END)
            except Exception:
                pass
            self._last_ai_insert_range = None
            self.add_confirmation_message("↶ Undone last AI insertion")
        except Exception as e:
            print("Undo last AI insertion error:", e)

    # --- Dragging and boundary clamp ---
    def _enable_drag_on(self, widget):
        try:
            self._drag_origin = {'x': 0, 'y': 0}
            self._is_dragging = False
            widget.bind("<ButtonPress-1>", self._on_drag_start, add='+')
            widget.bind("<B1-Motion>", self._on_drag_motion, add='+')
            widget.bind("<ButtonRelease-1>", self._on_drag_end, add='+')
        except Exception:
            pass

    def _on_drag_start(self, event):
        try:
            self._is_dragging = True
            # Store offset between cursor and window's top-left in root coords
            win_rx = self.modal_window.winfo_rootx()
            win_ry = self.modal_window.winfo_rooty()
            self._drag_offset_x = event.x_root - win_rx
            self._drag_offset_y = event.y_root - win_ry
        except Exception:
            pass

    def _on_drag_motion(self, event):
        try:
            # Desired top-left in root coords, keeping cursor at same offset
            desired_x = event.x_root - getattr(self, '_drag_offset_x', 0)
            desired_y = event.y_root - getattr(self, '_drag_offset_y', 0)
            w = self.modal_window.winfo_width()
            h = self.modal_window.winfo_height()
            cx, cy = self._clamp_within_parent(desired_x, desired_y, w, h)
            self.modal_window.wm_geometry(f"{w}x{h}+{cx}+{cy}")
        except Exception:
            pass

    def _on_drag_end(self, event):
        try:
            self._is_dragging = False
            self._drag_offset_x = 0
            self._drag_offset_y = 0
            self._clamp_modal()
        except Exception:
            pass

    def _on_parent_resize_or_state(self, event=None):
        try:
            # Close on minimize
            try:
                if hasattr(self.parent, 'state') and self.parent.state() == 'iconic':
                    self.hide_modal()
                    return
            except Exception:
                pass
            # Close on fullscreen
            try:
                if hasattr(self.parent, 'attributes') and bool(self.parent.attributes('-fullscreen')):
                    self.hide_modal()
                    return
            except Exception:
                pass
            # Otherwise clamp position inside window bounds
            self._clamp_modal()
        except Exception:
            pass

    def _clamp_modal(self):
        try:
            if not self.is_modal_visible():
                return
            w = self.modal_window.winfo_width()
            h = self.modal_window.winfo_height()
            # Toplevel winfo_x/y are already in root (screen) coordinates
            x = self.modal_window.winfo_x()
            y = self.modal_window.winfo_y()
            cx, cy = self._clamp_within_parent(x, y, w, h)
            self.modal_window.wm_geometry(f"{w}x{h}+{cx}+{cy}")
        except Exception:
            pass

    def _clamp_within_parent(self, abs_x: int, abs_y: int, w: int, h: int):
        try:
            px = self.parent.winfo_rootx()
            py = self.parent.winfo_rooty()
            pw = max(1, self.parent.winfo_width())
            ph = max(1, self.parent.winfo_height())
            min_x = px
            min_y = py
            max_x = px + max(0, pw - w)
            max_y = py + max(0, ph - h)
            nx = min(max(abs_x, min_x), max_x)
            ny = min(max(abs_y, min_y), max_y)
            return nx, ny
        except Exception:
            return abs_x, abs_y
        
    def show_table_dropdown(self):
        """Show table selection dropdown."""
        if not self.db_manager.current_db:
            return
            
        # Get cursor position
        cursor_pos = self.input_entry.index(tk.INSERT)
        bbox = self.input_entry.bbox(cursor_pos)
        if bbox is None:
            # Fallback position
            x, y = 0, 0
        else:
            x, y, width, height = bbox
            
        # Create dropdown window
        self.dropdown_window = tk.Toplevel(self.modal_window)
        self.dropdown_window.wm_overrideredirect(True)
        self.dropdown_window.wm_geometry(f"+{self.modal_window.winfo_rootx() + x}+{self.modal_window.winfo_rooty() + y + 25}")
        self.dropdown_window.configure(bg="#2d2d2d")
        self.dropdown_window.wm_attributes("-topmost", True)
        
        # Create dropdown frame
        dropdown_frame = tk.Frame(self.dropdown_window, bg="#2d2d2d", relief="raised", bd=1)
        dropdown_frame.pack()
        
        # Search entry
        search_frame = tk.Frame(dropdown_frame, bg="#2d2d2d")
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        search_entry = tk.Entry(search_frame, 
                               font=("Consolas", 9),
                               bg="#404040", fg="#ffffff",
                               insertbackground="#ffffff",
                               relief="flat", bd=0,
                               width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_entry.bind("<KeyRelease>", lambda e: self.filter_tables(search_entry.get()))
        
        # Table list
        list_frame = tk.Frame(dropdown_frame, bg="#2d2d2d")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Scrollbar
        list_scrollbar = ttk.Scrollbar(list_frame)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox
        self.table_listbox = tk.Listbox(list_frame, 
                                       font=("Consolas", 9),
                                       bg="#1e1e1e", fg="#ffffff",
                                       selectbackground="#007acc",
                                       selectforeground="#ffffff",
                                       yscrollcommand=list_scrollbar.set,
                                       height=8)
        self.table_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.config(command=self.table_listbox.yview)
        
        # Load tables
        self.load_tables()
        
        # Bind selection
        self.table_listbox.bind("<Double-1>", self.select_table)
        self.table_listbox.bind("<Return>", self.select_table)
        
        # Focus search
        search_entry.focus()
        self.current_dropdown_type = "table"
        
    def show_column_dropdown(self):
        """Show column selection dropdown."""
        if not self.db_manager.current_db or not self.selected_tables:
            return
            
        # Get cursor position
        cursor_pos = self.input_entry.index(tk.INSERT)
        bbox = self.input_entry.bbox(cursor_pos)
        if bbox is None:
            # Fallback position
            x, y = 0, 0
        else:
            x, y, width, height = bbox
            
        # Create dropdown window
        self.dropdown_window = tk.Toplevel(self.modal_window)
        self.dropdown_window.wm_overrideredirect(True)
        self.dropdown_window.wm_geometry(f"+{self.modal_window.winfo_rootx() + x}+{self.modal_window.winfo_rooty() + y + 25}")
        self.dropdown_window.configure(bg="#2d2d2d")
        self.dropdown_window.wm_attributes("-topmost", True)
        
        # Create dropdown frame
        dropdown_frame = tk.Frame(self.dropdown_window, bg="#2d2d2d", relief="raised", bd=1)
        dropdown_frame.pack()
        
        # Search entry
        search_frame = tk.Frame(dropdown_frame, bg="#2d2d2d")
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        search_entry = tk.Entry(search_frame, 
                               font=("Consolas", 9),
                               bg="#404040", fg="#ffffff",
                               insertbackground="#ffffff",
                               relief="flat", bd=0,
                               width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_entry.bind("<KeyRelease>", lambda e: self.filter_columns(search_entry.get()))
        
        # Column list
        list_frame = tk.Frame(dropdown_frame, bg="#2d2d2d")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Scrollbar
        list_scrollbar = ttk.Scrollbar(list_frame)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox
        self.column_listbox = tk.Listbox(list_frame, 
                                        font=("Consolas", 9),
                                        bg="#1e1e1e", fg="#ffffff",
                                        selectbackground="#007acc",
                                        selectforeground="#ffffff",
                                        yscrollcommand=list_scrollbar.set,
                                        height=8)
        self.column_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.config(command=self.column_listbox.yview)
        
        # Load columns
        self.load_columns()
        
        # Bind selection
        self.column_listbox.bind("<Double-1>", self.select_column)
        self.column_listbox.bind("<Return>", self.select_column)
        
        # Focus search
        search_entry.focus()
        self.current_dropdown_type = "column"
        
    def load_tables(self):
        """Load tables from database."""
        try:
            tables = self.db_manager.get_tables()
            self.table_listbox.delete(0, tk.END)
            
            for table in tables:
                # Get row count for display
                try:
                    columns, data = self.db_manager.get_table_data(table, limit=1)
                    row_count = len(data) if data else 0
                    display_text = f"📊 {table} ({row_count} rows)"
                except:
                    display_text = f"📊 {table}"
                
                self.table_listbox.insert(tk.END, display_text)
        except Exception as e:
            print(f"Error loading tables: {e}")
            
    def load_columns(self):
        """Load columns from selected tables."""
        try:
            self.column_listbox.delete(0, tk.END)
            
            for table in self.selected_tables:
                try:
                    columns, _ = self.db_manager.get_table_data(table, limit=1)
                    for column in columns:
                        display_text = f"📋 {table}.{column}"
                        self.column_listbox.insert(tk.END, display_text)
                except:
                    pass
        except Exception as e:
            print(f"Error loading columns: {e}")
            
    def filter_tables(self, search_text):
        """Filter tables based on search text."""
        if not search_text:
            self.load_tables()
            return
            
        try:
            tables = self.db_manager.get_tables()
            self.table_listbox.delete(0, tk.END)
            
            for table in tables:
                if search_text.lower() in table.lower():
                    try:
                        columns, data = self.db_manager.get_table_data(table, limit=1)
                        row_count = len(data) if data else 0
                        display_text = f"📊 {table} ({row_count} rows)"
                    except:
                        display_text = f"📊 {table}"
                    
                    self.table_listbox.insert(tk.END, display_text)
        except Exception as e:
            print(f"Error filtering tables: {e}")
            
    def filter_columns(self, search_text):
        """Filter columns based on search text."""
        if not search_text:
            self.load_columns()
            return
            
        try:
            self.column_listbox.delete(0, tk.END)
            
            for table in self.selected_tables:
                try:
                    columns, _ = self.db_manager.get_table_data(table, limit=1)
                    for column in columns:
                        if search_text.lower() in column.lower() or search_text.lower() in table.lower():
                            display_text = f"📋 {table}.{column}"
                            self.column_listbox.insert(tk.END, display_text)
                except:
                    pass
        except Exception as e:
            print(f"Error filtering columns: {e}")
            
    def select_table(self, event=None):
        """Select a table from the dropdown."""
        selection = self.table_listbox.curselection()
        if selection:
            display_text = self.table_listbox.get(selection[0])
            # Extract table name (remove emoji and row count)
            table_name = display_text.replace("📊 ", "").split(" (")[0]
            
            if table_name not in self.selected_tables:
                self.selected_tables.append(table_name)
                
            # Insert @table_name into input
            cursor_pos = self.input_entry.index(tk.INSERT)
            self.input_entry.insert(cursor_pos, f"@{table_name} ")
            
        self.hide_dropdown()
        
    def select_column(self, event=None):
        """Select a column from the dropdown."""
        selection = self.column_listbox.curselection()
        if selection:
            display_text = self.column_listbox.get(selection[0])
            # Extract column name (remove emoji)
            column_name = display_text.replace("📋 ", "")
            
            # Insert #column_name into input
            cursor_pos = self.input_entry.index(tk.INSERT)
            self.input_entry.insert(cursor_pos, f"#{column_name} ")
            
        self.hide_dropdown()
        
    def hide_dropdown(self):
        """Hide the current dropdown."""
        if self.dropdown_window and self.dropdown_window.winfo_exists():
            self.dropdown_window.destroy()
        self.dropdown_window = None
        self.current_dropdown_type = None
        
    def toggle_history(self):
        """Toggle conversation history visibility."""
        if self.history_frame.winfo_ismapped():
            self.history_frame.pack_forget()
            # Resize modal
            self.modal_window.wm_geometry(f"{self.modal_width}x{self.modal_height}")
        else:
            self.history_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
            # Resize modal
            self.modal_window.wm_geometry(f"{self.modal_width}x{self.modal_height + self.history_height}")
            
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        if hasattr(self, 'history_text'):
            self.history_text.config(state=tk.NORMAL)
            self.history_text.delete("1.0", tk.END)
            self.history_text.config(state=tk.DISABLED)
            
    def get_selected_text_from_editor(self):
        """Get selected text from the SQL editor and highlight it."""
        try:
            # Check if there's a selection in the editor
            if hasattr(self.sql_editor, 'editor'):
                selected_text = self.sql_editor.editor.get(tk.SEL_FIRST, tk.SEL_LAST)
                if selected_text:
                    # Highlight the selected text
                    sel_start = self.sql_editor.editor.index(tk.SEL_FIRST)
                    sel_end = self.sql_editor.editor.index(tk.SEL_LAST)
                    self.highlight_prompt_text(sel_start, sel_end)
                    return selected_text.strip()
        except tk.TclError:
            # No selection
            pass
        return None
    
    def add_to_history(self, user_input, ai_response):
        """Add interaction to conversation history."""
        self.conversation_history.append({
            'user': user_input,
            'ai': ai_response,
            'timestamp': time.time()
        })
        
        # Update history display
        if hasattr(self, 'history_text'):
            self.history_text.config(state=tk.NORMAL)
            self.history_text.insert(tk.END, f"👤 {user_input}\n")
            self.history_text.insert(tk.END, f"🤖 {ai_response}\n\n")
            self.history_text.see(tk.END)
            self.history_text.config(state=tk.DISABLED)
            
    def generate_sql(self):
        """Generate SQL using AI with both selection-based (edit) and full prompt (normal) flows."""
        # Reset per-trigger warning flag
        self.warning_active = False
        prompt = self.input_var.get().strip()
        # Show loading state
        self.input_entry.configure(state="disabled")
        self.input_var.set("🤖 Generating...")
        self.modal_window.update()
        try:
            # Check if selection mode is active
            if getattr(self, 'selection_mode', False) and (self.selection_text is not None):
                seltext = self.selection_text.strip()
                # Detect partial selection (heuristic): lacks semicolon OR ends with incomplete clause
                try:
                    st_up = seltext.strip().upper()
                    is_partial = (not seltext.strip().endswith(';')) or st_up.endswith(('FROM', 'WHERE', 'JOIN', 'ON', 'GROUP BY', 'ORDER BY'))
                except Exception:
                    is_partial = False
                # Partial selection -> predictive completion
                if is_partial:
                    banner = "🔍 Completing your SQL...\n\n"
                    er_text = self._get_er_text()
                    mentions_text = self._get_mentions_text()
                    base = self._build_context_text()
                    parts = [p for p in [base, er_text, mentions_text] if p]
                    context_text = "\n".join(parts)
                    ai_prompt = f"""
Complete the following partial SQL into a valid, executable SQLite query. Use context if relevant.

PARTIAL_SQL:
{seltext}

CONTEXT:
{context_text}

Return only the completed SQL, no explanations or code fences.
"""
                    schema = None
                    if self.db_manager and self.db_manager.current_db:
                        try:
                            tables = self.db_manager.get_tables()
                            table_schema = []
                            for t in tables:
                                try:
                                    cols, _ = self.db_manager.get_table_data(t, limit=1)
                                    table_schema.append({"table_name": t, "columns": [{"name": c, "type": "TEXT"} for c in cols]})
                                except:
                                    table_schema.append({"table_name": t, "columns": []})
                            schema = {"database_name": self.db_manager.current_db, "tables": table_schema, "relationships": []}
                        except Exception as e:
                            print(f"Schema (partial mode) error: {e}")
                    ai_sql = None
                    self.ai_response_pending = True
                    try:
                        self._debug_print_prompt(ai_prompt)
                        ai_sql = self.ai_integration.generate_sql_query(ai_prompt, schema)
                    except Exception as e:
                        print(f"AI error: {e}")
                    finally:
                        self.ai_response_pending = False
                    if not ai_sql or not str(ai_sql).strip():
                        self._warn_once("⚠️ No response generated. Try rephrasing your query.")
                        self.input_entry.configure(state="normal")
                        self.input_var.set("")
                        return
                    ai_sql_clean = self._clean_sql_display(ai_sql)
                    if not self._looks_like_sql(ai_sql_clean):
                        self._warn_once("⚠️ No SQL query detected. Try rephrasing your prompt.")
                        self.input_entry.configure(state="normal")
                        self.input_var.set("")
                        return
                    merged = f"{banner}{ai_sql_clean}\n"
                    self.add_chat_message("assistant", merged)
                    # Add suggestion with NEW only (no OLD)
                    self._add_suggestion_block("", ai_sql_clean)
                    self.input_entry.configure(state="normal")
                    self.input_var.set("")
                    if hasattr(self, 'chat_text'):
                        self.chat_text.see('end')
                    return
                # Valid selection (full SQL) -> existing edit flow with suggestion block
                # (unchanged below)
                # Strict validation for partial/invalid selection already routed above
                # Build banner and targeted prompt
                banner = "🧠 Editing selected code...\n\n"
                ai_prompt = f"""
Improve, fix, or optimize ONLY the following SQL query:

{seltext}

Return only the improved query, no explanations, code fences, or extra symbols.
"""
                # Prepare minimal schema (best-effort)
                schema = None
                if self.db_manager and self.db_manager.current_db:
                    try:
                        tables = self.db_manager.get_tables()
                        table_schema = []
                        for t in tables:
                            try:
                                cols, _ = self.db_manager.get_table_data(t, limit=1)
                                table_schema.append({"table_name": t, "columns": [{"name": c, "type": "TEXT"} for c in cols]})
                            except:
                                table_schema.append({"table_name": t, "columns": []})
                        schema = {"database_name": self.db_manager.current_db, "tables": table_schema, "relationships": []}
                    except Exception as e:
                        print(f"Schema (selection mode) error: {e}")
                # Include session context for incremental improvements
                # Add ER and mentions to context for selection-based edits
                er_text = self._get_er_text()
                mentions_text = self._get_mentions_text()
                base = self._build_context_text()
                parts = [p for p in [base, er_text, mentions_text] if p]
                context_text = "\n".join(parts)
                if context_text:
                    ai_prompt += f"\nCONTEXT:\n{context_text}\n"
                # Call AI
                ai_sql = None
                self.ai_response_pending = True
                try:
                    self._debug_print_prompt(ai_prompt)
                    ai_sql = self.ai_integration.generate_sql_query(ai_prompt, schema)
                except Exception as e:
                    print(f"AI error: {e}")
                finally:
                    self.ai_response_pending = False
                # Handle empty/missing response
                if not ai_sql or not str(ai_sql).strip():
                    self._warn_once("⚠️ No response generated. Try rephrasing your query.")
                    self.input_entry.configure(state="normal")
                    self.input_var.set("")
                    return
                # Clean and merge display
                ai_sql_clean = self._clean_sql_display(ai_sql)
                # Non-SQL detection on response
                if not self._looks_like_sql(ai_sql_clean):
                    self._warn_once("⚠️ No SQL query detected. Try rephrasing your prompt.")
                    self.input_entry.configure(state="normal")
                    self.input_var.set("")
                    return
                # If identical (ignoring whitespace and trailing semicolons), show no-change notice
                def _norm(s):
                    return (s or "").strip().rstrip(';').strip()
                if _norm(ai_sql_clean) == _norm(seltext):
                    self.add_chat_message("assistant", "No changes suggested for this selection.")
                    self.input_entry.configure(state="normal")
                    self.input_var.set("")
                    return
                # Merge banner + SQL as single assistant line before suggestion block
                merged = f"{banner}{ai_sql_clean}\n"
                # Determine selection positions (best-effort)
                sel_start, sel_end = None, None
                try:
                    sel_start = self.sql_editor.editor.index(tk.SEL_FIRST)
                    sel_end = self.sql_editor.editor.index(tk.SEL_LAST)
                except Exception:
                    pass
                # Show merged assistant text and suggestion block
                self.add_chat_message("assistant", merged, {
                    'old_code': seltext,
                    'new_code': ai_sql_clean,
                    'old_start': sel_start,
                    'old_end': sel_end
                })
                # Also show quick actions for convenience
                try:
                    self._create_inline_actions_bar(ai_sql_clean)
                except Exception:
                    pass
                self.input_entry.configure(state="normal")
                self.input_var.set("")
                if hasattr(self, 'chat_text'):
                    self.chat_text.see('end')
                return
            # ---Fallback: no selection, default full prompt mode---
            prompt_text = prompt
            schema = None
            if self.db_manager and self.db_manager.current_db:
                try:
                    tables = self.db_manager.get_tables()
                    table_schemas = []
                    for table_name in tables:
                        try:
                            columns, _ = self.db_manager.get_table_data(table_name, limit=1)
                            table_schemas.append({
                                "table_name": table_name,
                                "columns": [{"name": col, "type": "TEXT"} for col in columns]
                            })
                        except:
                            table_schemas.append({"table_name": table_name, "columns": []})
                    schema = {"database_name": self.db_manager.current_db, "tables": table_schemas, "relationships": []}
                except Exception as e:
                    print(f"Schema extraction error: {e}")
            # If empty prompt, start a draft using context (incl. full file) and schema
            if not prompt_text:
                banner = "🧠 Starting a new query draft...\n\n"
                file_ctx = self._get_file_context_snippet()
                context_base = self._build_context_text()
                er_text = self._get_er_text()
                mentions_text = self._get_mentions_text()
                convention = self._get_mention_convention_text()
                parts = [p for p in [context_base, er_text, mentions_text, convention, file_ctx] if p]
                context_text = "\n".join(parts)
                ai_prompt = f"""
Generate a relevant starter SQL query for this database. Use context if helpful.

CONTEXT:
{context_text}

Return only the SQL, no explanations or code fences.
"""
                ai_sql = None
                self.ai_response_pending = True
                try:
                    self._debug_print_prompt(ai_prompt)
                    ai_sql = self.ai_integration.generate_sql_query(ai_prompt, schema)
                except Exception as e:
                    print(f"AI error: {e}")
                finally:
                    self.ai_response_pending = False
                if not ai_sql or not str(ai_sql).strip():
                    self._warn_once("⚠️ No response generated. Try rephrasing your query.")
                    self.input_entry.configure(state="normal")
                    self.input_var.set("")
                    return
                ai_sql_clean = self._clean_sql_display(ai_sql)
                if not self._looks_like_sql(ai_sql_clean):
                    self._warn_once("⚠️ No SQL query detected. Try rephrasing your prompt.")
                    self.input_entry.configure(state="normal")
                    self.input_var.set("")
                    return
                merged = f"{banner}{ai_sql_clean}\n"
                self.add_chat_message("assistant", merged)
                # Explicitly add compact Keep/Reject
                try:
                    self._add_suggestion_block("", ai_sql_clean)
                except Exception:
                    pass
                self.input_entry.configure(state="normal")
                self.input_var.set("")
                if hasattr(self, 'chat_text'):
                    self.chat_text.see('end')
                return
            # If non-SQL prompt, convert natural language to SQL (use full file as context too)
            if not self._looks_like_sql(prompt_text):
                file_ctx = self._get_file_context_snippet()
                context_base = self._build_context_text()
                er_text = self._get_er_text()
                mentions_text = self._get_mentions_text()
                convention = self._get_mention_convention_text()
                parts = [p for p in [context_base, er_text, mentions_text, convention, file_ctx] if p]
                context_text = "\n".join(parts)
                norm_instruction = self._normalize_mentions(prompt_text)
                ai_prompt = f"""
Modify or extend the previous SQL based on this instruction (mentions already normalized as [[TABLE:]] and {{COLUMN:}}):

INSTRUCTION: {norm_instruction}

CONTEXT:
{context_text}

Return only the final SQL, no explanations or code fences.
"""
                ai_sql = None
                self.ai_response_pending = True
                try:
                    self._debug_print_prompt(ai_prompt)
                    ai_sql = self.ai_integration.generate_sql_query(ai_prompt, schema)
                except Exception as e:
                    print(f"AI error: {e}")
                finally:
                    self.ai_response_pending = False
                # Show user instruction then assistant single SQL line
                self.add_chat_message("user", prompt_text)
                if not ai_sql or not str(ai_sql).strip():
                    self._warn_once("⚠️ No response generated. Try rephrasing your query.")
                    self.input_entry.configure(state="normal")
                    self.input_var.set("")
                    return
                ai_sql_clean = self._clean_sql_display(ai_sql)
                self.add_chat_message("assistant", ai_sql_clean)
                # Explicitly add compact Keep/Reject
                try:
                    self._add_suggestion_block("", ai_sql_clean)
                except Exception:
                    pass
                self.input_entry.configure(state="normal")
                self.input_var.set("")
                if hasattr(self, 'chat_text'):
                    self.chat_text.see('end')
                return
            # Otherwise, treat as direct SQL text and refine
            norm_request = self._normalize_mentions(prompt_text)
            enhanced_prompt = f"""Generate a complete, executable SQL query for: {norm_request}

Requirements:
- Return ONLY the SQL query, no explanations
- Ensure the query is complete and ends with semicolon
- Use proper SQLite syntax
{f"- Database context: {self.db_manager.current_db}" if self.db_manager and self.db_manager.current_db else ""}
"""
            # Include context for continuity even in plain mode (and include full file)
            file_ctx = self._get_file_context_snippet()
            er_text = self._get_er_text()
            mentions_text = self._get_mentions_text()
            context_base = self._build_context_text()
            convention = self._get_mention_convention_text()
            parts = [p for p in [context_base, er_text, mentions_text, convention, file_ctx] if p]
            context_text = "\n".join(parts)
            if context_text:
                enhanced_prompt += f"\nCONTEXT:\n{context_text}\n"
            ai_sql = None
            self.ai_response_pending = True
            try:
                self._debug_print_prompt(enhanced_prompt)
                ai_sql = self.ai_integration.generate_sql_query(enhanced_prompt, schema)
            except Exception as e:
                print(f"AI error: {e}")
            finally:
                self.ai_response_pending = False
            # Assistant line should always show user request
            self.add_chat_message("user", prompt_text)
            if not ai_sql or not str(ai_sql).strip():
                self._warn_once("⚠️ No response generated. Try rephrasing your query.")
                self.input_entry.configure(state="normal")
                self.input_var.set("")
                return
            ai_sql_clean = self._clean_sql_display(ai_sql)
            if not self._looks_like_sql(ai_sql_clean):
                self._warn_once("⚠️ No SQL query detected. Try rephrasing your prompt.")
                self.input_entry.configure(state="normal")
                self.input_var.set("")
                return
            # Plain generated SQL: show line and explicit compact Keep/Reject
            self.add_chat_message("assistant", ai_sql_clean)
            try:
                self._add_suggestion_block("", ai_sql_clean)
            except Exception:
                pass
            self.input_entry.configure(state="normal")
            self.input_var.set("")
            if hasattr(self, 'chat_text'):
                self.chat_text.see('end')
        except Exception as e:
            print(f"Error in generate_sql: {e}")
            self.add_chat_message("assistant", f"⚠️ Error: {str(e)}")
            self.input_entry.configure(state="normal")
            self.input_var.set("")
            
    # Old confirmation prompt method - now replaced by inline Keep/Discard buttons
    # def show_confirmation_prompt(self, generated_sql, selected_text=None):
            
    def apply_sql(self, sql):
        """Apply generated SQL to the editor."""
        self.sql_editor.editor.delete("1.0", tk.END)
        self.sql_editor.editor.insert("1.0", sql)
        
        # Highlight the entire replaced content
        end_pos = self.sql_editor.editor.index(f"1.0+{len(sql)}c")
        self.highlight_replaced_text("1.0", end_pos)
    
    def insert_at_cursor(self, sql):
        """Insert SQL at the current cursor position with proper spacing."""
        cursor_pos = self.sql_editor.editor.index(tk.INSERT)
        text = self._compute_gapped_text(cursor_pos, sql)
        self.sql_editor.editor.insert(cursor_pos, text)
        new_end = self.sql_editor.editor.index(f"{cursor_pos}+{len(text)}c")
        self.highlight_replaced_text(cursor_pos, new_end)
    
    # Removed is_query_complete - no longer needed, we let the AI return what it can
    
    def highlight_replaced_text(self, start_pos, end_pos):
        """Highlight replaced/inserted text with a special color."""
        try:
            # Configure highlighting tags
            self.sql_editor.editor.tag_configure("ai_replaced", 
                                                background="#2d4a2d",  # Dark green background
                                                foreground="#90EE90",  # Light green text
                                                relief="raised",
                                                borderwidth=1)
            
            # Apply the highlight tag
            self.sql_editor.editor.tag_add("ai_replaced", start_pos, end_pos)
            
            # Auto-remove highlight after 5 seconds
            try:
                if self.modal_window and self.modal_window.winfo_exists():
                    self.modal_window.after(5000, lambda: self.remove_highlight("ai_replaced"))
                else:
                    self.sql_editor.editor.after(5000, lambda: self.remove_highlight("ai_replaced"))
            except Exception:
                self.sql_editor.editor.after(5000, lambda: self.remove_highlight("ai_replaced"))
            
        except Exception as e:
            print(f"Error highlighting text: {e}")
    
    def highlight_prompt_text(self, start_pos, end_pos):
        """Persistently highlight text sent to AI in orange until removed by the user."""
        try:
            self.sql_editor.editor.tag_configure("ai_prompt",
                                                background="#ff8c00",  # Orange background
                                                foreground="#000000",
                                                relief="flat",
                                                borderwidth=0)
            self.sql_editor.editor.tag_add("ai_prompt", start_pos, end_pos)
        except Exception as e:
            print(f"Error highlighting prompt text: {e}")
    
    def remove_highlight(self, tag_name):
        """Remove highlighting from text."""
        try:
            self.sql_editor.editor.tag_remove(tag_name, "1.0", tk.END)
        except Exception as e:
            print(f"Error removing highlight: {e}")
    
    def remove_all_highlights(self):
        """Remove all AI-related highlights."""
        try:
            self.sql_editor.editor.tag_remove("ai_selected", "1.0", tk.END)
            self.sql_editor.editor.tag_remove("ai_replaced", "1.0", tk.END)
            # Do not auto-remove ai_prompt; it's persistent until user drops it
        except Exception as e:
            print(f"Error removing highlights: {e}")
    
    def on_editor_click(self, event):
        """Handle click events in the SQL editor to remove highlights."""
        self.remove_all_highlights()
    
    def on_editor_key(self, event):
        """Handle key events in the SQL editor to remove highlights."""
        self.remove_all_highlights()

    def on_editor_double_click(self, event):
        """Drop orange prompt highlight on double-click inside it."""
        try:
            idx = self.sql_editor.editor.index(f"@{event.x},{event.y}")
            for i in range(0, 100):  # iterate tag ranges safely
                ranges = self.sql_editor.editor.tag_ranges("ai_prompt")
                if not ranges:
                    return
                # ranges are start1, end1, start2, end2, ...
                hit = False
                for j in range(0, len(ranges), 2):
                    s = str(ranges[j])
                    e = str(ranges[j+1])
                    if self.sql_editor.editor.compare(idx, ">=", s) and self.sql_editor.editor.compare(idx, "<=", e):
                        self.sql_editor.editor.tag_remove("ai_prompt", s, e)
                        hit = True
                        break
                if not hit:
                    break
        except Exception:
            pass

    def on_editor_selection_release(self, event):
        """If user over-selects beyond orange highlight, drop it."""
        try:
            if not self.sql_editor.editor.tag_ranges(tk.SEL):
                return
            sel_start = self.sql_editor.editor.index(tk.SEL_FIRST)
            sel_end = self.sql_editor.editor.index(tk.SEL_LAST)
            ranges = self.sql_editor.editor.tag_ranges("ai_prompt")
            if not ranges:
                return
            # If selection extends outside any prompt range, remove those ranges
            for j in range(0, len(ranges), 2):
                s = str(ranges[j])
                e = str(ranges[j+1])
                over_left = self.sql_editor.editor.compare(sel_start, "<", s)
                over_right = self.sql_editor.editor.compare(sel_end, ">", e)
                if over_left or over_right:
                    self.sql_editor.editor.tag_remove("ai_prompt", s, e)
        except Exception:
            pass
    
    # Removed try_alternative_generation and handle_incomplete_query - no longer needed
    # These methods caused UI spam with retry messages
    
    def replace_selected_text(self, sql):
        """Replace selected text in the editor with generated SQL."""
        try:
            # Add proper spacing to SQL
            sql = sql.strip()
            
            # Check if there's a selection
            if self.sql_editor.editor.tag_ranges(tk.SEL):
                # Get selection range for highlighting
                sel_start = self.sql_editor.editor.index(tk.SEL_FIRST)
                sel_end = self.sql_editor.editor.index(tk.SEL_LAST)
                
                # Replace the selected text
                self.sql_editor.editor.delete(tk.SEL_FIRST, tk.SEL_LAST)
                insert_pos = self.sql_editor.editor.index(tk.INSERT)
                text = self._compute_gapped_text(insert_pos, sql)
                self.sql_editor.editor.insert(tk.INSERT, text)
                
                # Calculate new end position after insertion
                new_end = self.sql_editor.editor.index(f"{insert_pos}+{len(text)}c")
                
                # Highlight the replaced text with a different color
                self.highlight_replaced_text(insert_pos, new_end)
                # Tag for undo
                try:
                    self.sql_editor.editor.tag_remove("ai_last_insert", "1.0", tk.END)
                except Exception:
                    pass
                self.sql_editor.editor.tag_add("ai_last_insert", insert_pos, new_end)
                self._last_ai_insert_range = (insert_pos, new_end)
            else:
                # No selection, insert at cursor position
                cursor_pos = self.sql_editor.editor.index(tk.INSERT)
                text = self._compute_gapped_text(cursor_pos, sql)
                self.sql_editor.editor.insert(cursor_pos, text)
                
                # Highlight the inserted text
                new_end = self.sql_editor.editor.index(f"{cursor_pos}+{len(text)}c")
                self.highlight_replaced_text(cursor_pos, new_end)
                # Tag for undo
                try:
                    self.sql_editor.editor.tag_remove("ai_last_insert", "1.0", tk.END)
                except Exception:
                    pass
                self.sql_editor.editor.tag_add("ai_last_insert", cursor_pos, new_end)
                self._last_ai_insert_range = (cursor_pos, new_end)
        except tk.TclError:
            # Fallback: insert at cursor position
            cursor_pos = self.sql_editor.editor.index(tk.INSERT)
            text = self._compute_gapped_text(cursor_pos, sql)
            self.sql_editor.editor.insert(cursor_pos, text)
            
            # Highlight the inserted text
            new_end = self.sql_editor.editor.index(f"{cursor_pos}+{len(text)}c")
            self.highlight_replaced_text(cursor_pos, new_end)
            # Tag for undo
            try:
                self.sql_editor.editor.tag_remove("ai_last_insert", "1.0", tk.END)
            except Exception:
                pass
            self.sql_editor.editor.tag_add("ai_last_insert", cursor_pos, new_end)
            self._last_ai_insert_range = (cursor_pos, new_end)
        
    # Old popup methods removed - now using inline chat interface
    # def show_sql_popup(self, sql):
    # def copy_to_editor(self, sql, popup):
    # def _show_error(self, message):
        
    def hide_modal(self):
        """Hide the modal and clear chat if configured."""
        if not self.is_visible or not self.modal_window:
            return
            
        self.is_visible = False
        self.chat_expanded = False
        
        # Clear conversation history on close
        self.conversation_history = []
        self.chat_messages = []
        self.suggestion_buttons = {}
        self.inline_buttons = {}
        
        # Clear chat text if it exists
        if hasattr(self, 'chat_text'):
            self.chat_text.delete("1.0", tk.END)
        
        # Reset session context
        self.session_context = []
        
        # Remove all highlights
        if hasattr(self.sql_editor, 'editor'):
            self.sql_editor.editor.tag_remove("ai_old", "1.0", tk.END)
            self.sql_editor.editor.tag_remove("ai_applied", "1.0", tk.END)
        
        if self.modal_window and self.modal_window.winfo_exists():
            self.modal_window.destroy()
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
        
    def show_at_cursor(self, event):
        """Show modal at cursor position."""
        self.show_modal(event=event)
        
    def show_at_position(self, x, y):
        """Show modal at specific position."""
        self.show_modal(position=(x, y))
        
    def toggle_modal(self, event=None):
        """Toggle modal visibility."""
        if self.is_visible:
            self.hide_modal()
        else:
            self.show_modal(event)
            
    def is_modal_visible(self):
        """Check if modal is currently visible."""
        return self.is_visible and self.modal_window and self.modal_window.winfo_exists()

    def _clean_sql_display(self, sql_text):
        """Clean code fences and trailing punctuation for AI SQL responses shown inline."""
        if not isinstance(sql_text, str):
            return sql_text
        text = sql_text.strip()
        if not text:
            return text
        # Remove common markdown fences
        text = text.replace("```sql", "").replace("```", "").strip()
        # Drop any standalone fence lines or empty lines from the ends
        lines = [l for l in text.splitlines() if l.strip() not in ("```sql", "```", "")]
        cleaned = "\n".join(lines).strip('`\"\' + " ')
        # Normalize trailing semicolons: collapse duplicates and ensure single if needed
        while cleaned.endswith(";;"):
            cleaned = cleaned[:-1].strip()
        if cleaned and not cleaned.endswith(';'):
            cleaned += ';'
        return cleaned

    def _show_selection_mode_label(self, parent):
        # Place a label above the chat area in the modal if we're in selection mode
        try:
            label = tk.Label(parent, text='🧠 Editing selected code...',
                             bg="#2d2d2d", fg="#17a2b8",
                             font=("Arial", 9, "italic"), anchor="w")
            label.pack(fill=tk.X, padx=6, pady=(3, 0), before=self.chat_frame.winfo_children()[0] if self.chat_frame.winfo_children() else None)
            # Store for later hide (if needed)
            self.selection_mode_label = label
        except Exception as e:
            print("Couldn't show selection mode label:", e)
    
    def _hide_selection_mode_label(self):
        if hasattr(self, 'selection_mode_label') and self.selection_mode_label:
            self.selection_mode_label.destroy()
            self.selection_mode_label = None

    def _is_valid_sql_selection(self, text):
        """Check if selected text looks like a valid SQL query or statement."""
        if not text or not isinstance(text, str):
            return False
        lowered = text.strip().lower()
        sql_keywords = ['select', 'insert', 'update', 'delete', 'create', 'alter', 'drop']
        if any(k in lowered for k in sql_keywords) and ';' in lowered:
            return True
        # Also allow single-line non-semicolon cases (e.g. CREATE TABLE ...)
        if any(lowered.startswith(k) for k in sql_keywords) and len(lowered) > 10:
            return True
        return False

    def _looks_like_sql(self, text):
        """Heuristic check: does the text contain typical SQL patterns?"""
        try:
            if not text or not isinstance(text, str):
                return False
            up = text.upper()
            patterns = [
                'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP',
                'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'JOIN'
            ]
            return any(p in up for p in patterns)
        except Exception:
            return False

    def _warn_once(self, message_text):
        try:
            if getattr(self, 'warning_active', False) or getattr(self, 'ai_response_pending', False):
                return
            self.add_chat_message("assistant", message_text)
            self.warning_active = True
        except Exception:
            pass

    def _auto_resize_chat(self):
        """Adjust modal height based on chat content up to a max, to keep UI compact."""
        try:
            # Prefer precise pixel count for full content height
            total_pixels = 0
            try:
                total_pixels = int(self.chat_text.count("1.0", "end", "ypixels")[0])
            except Exception:
                # Fallback to last line metrics if count unsupported
                info = self.chat_text.dlineinfo("end-1c")
                if not info:
                    return
                _, y, _, h, _, _ = info
                total_pixels = y + h + 6
            current_height = self.modal_window.winfo_height()
            extra = max(total_pixels, self._min_chat_extra_px)
            target_extra = min(extra, self._max_chat_extra_px)
            target_height = self._base_modal_height + target_extra
            if abs(current_height - target_height) > 4:
                self.modal_window.after_idle(lambda: self.modal_window.wm_geometry(f"{self.modal_width}x{target_height}"))
        except Exception:
            pass

    def _resize_to_content(self):
        """Public helper to trigger content-based resize after UI settles (visual only)."""
        try:
            # Allow geometry to stabilize, then compute and apply target height
            self.modal_window.after(10, self._auto_resize_chat)
        except Exception:
            pass

    def _build_context_text(self):
        """Return a concise text representation of recent chat context for AI prompts."""
        try:
            if not self.session_context:
                return ""
            lines = []
            for item in self.session_context[-self._max_context_items:]:
                role = item.get('role', 'user')
                content = (item.get('content') or '').strip()
                if not content:
                    continue
                prefix = 'USER' if role == 'user' else 'ASSISTANT'
                lines.append(f"{prefix}: {content}")
            return "\n".join(lines[-self._max_context_items:])
        except Exception:
            return ""

    def _get_file_context_snippet(self) -> str:
        """Return a trimmed CURRENT_FILE section from the editor, or empty string if unavailable."""
        try:
            if not hasattr(self.sql_editor, 'editor'):
                return ""
            text = (self.sql_editor.editor.get("1.0", tk.END) or '').strip()
            if not text:
                return ""
            max_chars = 4000
            snippet = text if len(text) <= max_chars else text[:max_chars] + "\n..."
            return "CURRENT_FILE:\n" + snippet
        except Exception:
            return ""

    def _get_er_text(self) -> str:
        """Return ER relationships from the current DB as readable lines."""
        try:
            if not self.db_manager or not self.db_manager.current_db:
                return ""
            tables = self.db_manager.get_tables()
            rels = []
            for t in tables:
                try:
                    # Use SQLite pragma to list foreign keys
                    self.db_manager.cursor.execute(f"PRAGMA foreign_key_list({t})")
                    for fk in self.db_manager.cursor.fetchall():
                        # fk: (id, seq, table, from, to, on_update, on_delete, match)
                        rels.append((t, fk[3], fk[2], fk[4]))
                except Exception:
                    continue
            if not rels:
                return ""
            lines = ["ER (Foreign Keys):"]
            for fr_table, fr_col, to_table, to_col in rels:
                lines.append(f"  - {fr_table}.{fr_col} -> {to_table}.{to_col}")
            return "\n".join(lines)
        except Exception:
            return ""

    def _get_mentions_text(self) -> str:
        """Explain @table and #table:column mentions detected in the current input."""
        try:
            text = (self.input_var.get() or "").strip()
            if not text:
                return ""
            mentions = []
            # @table tokens (letters, numbers, underscores)
            for m in re.findall(r"@([A-Za-z0-9_]+)", text):
                mentions.append(f"@{m} means table '{m}'")
            # #table:column tokens
            for m in re.findall(r"#([A-Za-z0-9_]+):([A-Za-z0-9_]+)", text):
                tbl, col = m
                mentions.append(f"#{tbl}:{col} means column '{col}' in table '{tbl}'")
            if not mentions:
                return ""
            header = "Mentions:"
            return header + "\n" + "\n".join(["  - " + s for s in mentions])
        except Exception:
            return ""

    def _get_mention_convention_text(self) -> str:
        try:
            return (
                "Convention for database references:\n"
                "  - Tables are written as [[TABLE:name]]\n"
                "  - Columns are written as {{COLUMN:table.column}}\n"
                "Please respect these tags when generating SQL."
            )
        except Exception:
            return ""

    def _normalize_mentions(self, text: str) -> str:
        try:
            if not text:
                return text
            # Columns first: #table:column -> {{COLUMN:table.column}}
            text = re.sub(r"#([A-Za-z0-9_]+):([A-Za-z0-9_]+)", r"{{COLUMN:\1.\2}}", text)
            # Tables next: @table -> [[TABLE:table]]
            text = re.sub(r"@([A-Za-z0-9_]+)", r"[[TABLE:\1]]", text)
            return text
        except Exception:
            return text

    def _add_suggestion_block(self, old_code, new_code, old_start=None, old_end=None):
        """Render a suggestion block using existing chat insertion. OLD may be empty."""
        try:
            suggestion_data = {
                'old_code': old_code if old_code else None,
                'new_code': new_code,
                'old_start': old_start,
                'old_end': old_end
            }
            # Use assistant message with suggestion data (existing path)
            self.add_chat_message("assistant", "", suggestion_data)
        except Exception:
            pass
