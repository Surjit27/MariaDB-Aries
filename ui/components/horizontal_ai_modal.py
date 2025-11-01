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
    
    def _extract_clean_error_message(self, error: Exception) -> str:
        """Extract clean error message from AI exception, removing metadata and formatting."""
        error_str = str(error)
        
        # Try to extract message from Google API error format
        # Format: metadata {...}, locale: "...", message: "actual message"
        import re
        
        # Look for message field in the error string
        message_match = re.search(r'message:\s*"([^"]+)"', error_str, re.IGNORECASE)
        if message_match:
            return message_match.group(1)
        
        # Look for common error patterns
        patterns = [
            r'"([^"]+API key[^"]+)"',  # API key related messages in quotes
            r'message:\s*([^\n,}]+)',  # message: followed by text
            r'Error:\s*([^\n]+)',      # Error: followed by text
            r'([A-Z][^"]{20,200})',    # Capitalized sentence (20-200 chars)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_str, re.IGNORECASE | re.MULTILINE)
            if match:
                clean_msg = match.group(1).strip()
                # Remove common prefixes/suffixes
                clean_msg = re.sub(r'^(error|exception|failed):\s*', '', clean_msg, flags=re.IGNORECASE)
                clean_msg = clean_msg.strip('.,;:')
                if len(clean_msg) > 10 and len(clean_msg) < 500:  # Reasonable message length
                    return clean_msg
        
        # Fallback: return first meaningful sentence
        sentences = re.split(r'[.!?]\s+', error_str)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 300:
                # Remove metadata indicators
                if not any(indicator in sentence.lower() for indicator in ['metadata', 'locale', 'key:', 'value:', 'traceback']):
                    return sentence
        
        # Last resort: return first 200 chars, cleaned up
        clean = error_str[:200].strip()
        clean = re.sub(r'\s+', ' ', clean)  # Normalize whitespace
        return clean if clean else "An error occurred"
    
    def _handle_ai_error(self, error: Exception):
        """Handle AI errors, especially API key errors, displaying in chat."""
        # Extract clean error message
        clean_error_msg = self._extract_clean_error_message(error)
        error_msg_lower = clean_error_msg.lower()
        
        print(f"AI error (clean): {clean_error_msg}")
        
        # Build error message for chat
        if any(keyword in error_msg_lower for keyword in ['api key', 'api_key', 'invalid', 'unauthorized', '403', '401', 'permission', 'authentication', 'not valid']):
            # API key error - provide helpful message
            error_content = f"❌ API Key Error\n\n{clean_error_msg}\n\n" \
                          f"📝 To fix this:\n" \
                          f"1. Go to Settings → API Keys\n" \
                          f"2. Check or update your Gemini API key\n" \
                          f"3. Make sure the key is valid and active\n" \
                          f"4. Get a new key from: https://aistudio.google.com/apikey"
        else:
            # Other AI errors
            error_content = f"❌ AI Error\n\n{clean_error_msg}"
        
        # Add error message to chat directly
        if hasattr(self, 'chat_text') and self.chat_text:
            self.add_chat_message("assistant", error_content)
        
        # Also show warning in input field
        self._warn_once(f"⚠️ {clean_error_msg[:50]}")
        
    def show_modal(self, event=None, position=None):
        """Show the horizontal AI modal with smart positioning and selection mode detection."""
        if self.is_visible:
            self.hide_modal()
            return
        self.is_visible = True

        # Detect SQL selection (both selected text and highlighted text)
        self.selection_text = None
        self.selection_mode = False
        self.is_highlighted_text = False  # Track if it's highlighted vs selected
        try:
            # First check for manually highlighted text (Ctrl+/ highlights)
            highlighted_text = self.get_highlighted_text_from_editor()
            if highlighted_text:
                self.selection_text = highlighted_text
                self.selection_mode = True
                self.is_highlighted_text = True
            else:
                # Fallback to regular selection
                sel = self.get_selected_text_from_editor()
                if sel and self._is_valid_sql_selection(sel):
                    self.selection_text = sel
                    self.selection_mode = True
                    self.is_highlighted_text = False
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
        
        # Pre-fill input with highlighted/selected text if available
        if self.selection_text:
            query_type = "highlighted" if getattr(self, 'is_highlighted_text', False) else "selected"
            initial_prompt = f"Please help me with this {query_type} query:\n\n{self.selection_text}"
            self.input_var.set(initial_prompt)
        
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
        
        # Text widget with rich text support - white background for black text
        # Make it read-only so users can't edit the AI responses
        self.chat_text = tk.Text(chat_container, 
                                 bg="#ffffff",  # White background
                                 fg="#000000",  # Black text for visibility
                                 font=("Consolas", 9),
                                 wrap=tk.WORD,
                                 yscrollcommand=self.chat_scrollbar.set,
                                 highlightthickness=0,
                                 relief="flat",
                                 bd=0,
                                 state=tk.DISABLED)  # Make read-only
        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=0, pady=0)
        self.chat_scrollbar.config(command=self.chat_text.yview)
        
        # Configure text tags for styling
        self.configure_chat_tags()
        
        # Button tracking for inline suggestions
        self.inline_buttons = {}
    
    def _safe_chat_insert(self, position, text, tags=None):
        """Safely insert text into read-only chat widget by temporarily enabling it."""
        try:
            self.chat_text.config(state=tk.NORMAL)
            if tags:
                self.chat_text.insert(position, text, tags)
            else:
                self.chat_text.insert(position, text)
            self.chat_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"Error inserting text into chat: {e}")
            try:
                self.chat_text.config(state=tk.DISABLED)  # Ensure it's disabled on error
            except:
                pass
    
    def _safe_chat_delete(self, start, end):
        """Safely delete text from read-only chat widget by temporarily enabling it."""
        try:
            self.chat_text.config(state=tk.NORMAL)
            self.chat_text.delete(start, end)
            self.chat_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"Error deleting text from chat: {e}")
            try:
                self.chat_text.config(state=tk.DISABLED)  # Ensure it's disabled on error
            except:
                pass
    
    def _safe_chat_get(self, start, end):
        """Safely get text from read-only chat widget."""
        try:
            return self.chat_text.get(start, end)
        except Exception as e:
            print(f"Error getting text from chat: {e}")
            return ""
        
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
        
        # Content tags - black text for better visibility on white background
        self.chat_text.tag_configure("normal_text", 
                                     foreground="#000000",  # Black text
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
        self._safe_chat_insert(tk.END, f"{role_emoji} {role.upper()}: ", role_tag)
        
        # If suggestion_data is provided AND content is empty, skip showing content
        # (the suggestion block will display it instead)
        # Only show content if there's no suggestion_data, OR if content is non-empty and different from suggestion's new_code
        should_show_content = True
        if suggestion_data and suggestion_data.get('new_code'):
            # If content matches the new_code in suggestion, don't show it twice
            if not content or content.strip() == suggestion_data.get('new_code', '').strip():
                should_show_content = False
        
        # Insert content (only if not duplicated in suggestion block)
        if should_show_content:
            self._safe_chat_insert(tk.END, f"{content}\n", "normal_text")
        else:
            # Just add a newline after the role header
            self._safe_chat_insert(tk.END, "\n", "normal_text")
        
        # Record in rolling session context (use content or suggestion's new_code)
        context_content = content
        if suggestion_data and suggestion_data.get('new_code') and not context_content:
            context_content = suggestion_data.get('new_code')
        
        try:
            self.session_context.append({'role': role, 'content': context_content})
            if len(self.session_context) > self._max_context_items:
                self.session_context = self.session_context[-self._max_context_items:]
        except Exception:
            pass
        
        # Add suggestion with inline buttons if provided
        if suggestion_data:
            self.add_code_suggestion_inline(suggestion_data)
        
        # Scroll to bottom and auto-resize (visual only)
        try:
            self.chat_text.config(state=tk.NORMAL)
            self.chat_text.see(tk.END)
            self.chat_text.config(state=tk.DISABLED)
        except Exception:
            pass
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
        
        # If assistant returned SQL with suggestion_data, show compact Keep/Reject actions
        # NOTE: Do NOT auto-add suggestion block here - let the caller decide when to add it
        # This prevents duplicate suggestion blocks when _add_suggestion_block is called explicitly
        try:
            if role == "assistant":
                if suggestion_data and suggestion_data.get('new_code'):
                    # Suggestion already rendered via add_code_suggestion_inline; nothing else needed
                    pass
                # Removed auto-suggestion block for plain SQL - caller should explicitly call _add_suggestion_block
                # This prevents duplication when suggestion_block is added explicitly after add_chat_message
        except Exception:
            pass
    
    def add_code_suggestion_inline(self, suggestion_data):
        """Add code suggestion inline with Keep/Discard buttons using window_create."""
        # Highlight old code in editor (red) if replacing existing code
        if suggestion_data.get('old_start') and suggestion_data.get('old_end'):
            self.highlight_old_code(suggestion_data['old_start'], suggestion_data['old_end'])
        
        # Add separator line
        self._safe_chat_insert(tk.END, "─" * 60 + "\n", "separator")
        
        # Add AI Suggestion label
        self._safe_chat_insert(tk.END, "💡 AI Suggestion:\n", "ai_suggestion_label")
        
        # Add explanation if available (from suggestion_data)
        if suggestion_data.get('explanation'):
            explanation = suggestion_data['explanation']
            # Format explanation nicely (wrap to 3-4 lines if needed)
            self._safe_chat_insert(tk.END, f"📝 Explanation: ", "ai_suggestion_label")
            self._safe_chat_insert(tk.END, f"{explanation}\n\n", "normal_text")
        else:
            # If no explanation provided by AI, add a default brief explanation
            # This helps users understand what the query does
            if suggestion_data.get('new_code'):
                self._safe_chat_insert(tk.END, f"📝 Explanation: ", "ai_suggestion_label")
                default_explanation = "This SQL query will be inserted into your editor. Review it and click Keep to apply or Reject to discard."
                self._safe_chat_insert(tk.END, f"{default_explanation}\n\n", "normal_text")
        
        # Add old code (if exists) - only show if there's existing code to replace
        if suggestion_data.get('old_code') and suggestion_data['old_code']:
            old_code = suggestion_data['old_code']
            if len(old_code) > 100:
                old_code = old_code[:100] + "..."
            self._safe_chat_insert(tk.END, f"OLD: ", "ai_suggestion_label")
            self._safe_chat_insert(tk.END, f"{old_code}\n", "old_code")
        
        # Add new code - this should always exist
        if suggestion_data.get('new_code'):
            new_code = suggestion_data['new_code']
            # Always show NEW label even if no OLD
            self._safe_chat_insert(tk.END, f"NEW: ", "ai_suggestion_label")
            self._safe_chat_insert(tk.END, f"{new_code}\n", "new_code")
        
        # Tight spacer before buttons
        self._safe_chat_insert(tk.END, "\n", "normal_text")
        
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
        # Store the position before inserting buttons so we can replace them later
        try:
            self.chat_text.config(state=tk.NORMAL)
            button_start_pos = self.chat_text.index(tk.END)
            
            keep_btn_ref = keep_btn
            discard_btn_ref = discard_btn
            # Now that refs exist, bind commands
            keep_btn_ref.configure(command=lambda s=suggestion_data, kb=keep_btn_ref, rb=discard_btn_ref: self._compact_keep_action(s, kb, rb, button_start_pos))
            discard_btn_ref.configure(command=lambda s=suggestion_data, kb=keep_btn_ref, rb=discard_btn_ref: self._compact_reject_action(s, kb, rb, button_start_pos))

            self.chat_text.window_create(tk.END, window=keep_btn_ref)
            self.chat_text.insert(tk.END, "    ")
            self.chat_text.window_create(tk.END, window=discard_btn_ref)
            button_end_pos = self.chat_text.index(tk.END)
            self.chat_text.insert(tk.END, "\n", "normal_text")
            self.chat_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"Error inserting buttons: {e}")
            try:
                self.chat_text.config(state=tk.DISABLED)
            except:
                pass
        
        # Store button references for tracking
        suggestion_id = f"suggestion_{len(self.chat_messages)}"
        self.inline_buttons[suggestion_id] = {
            'keep': keep_btn_ref,
            'discard': discard_btn_ref,
            'data': suggestion_data,
            'button_start': button_start_pos,
            'button_end': button_end_pos
        }
        
        # Auto-resize after adding suggestion (visual only)
        self._auto_resize_chat()
        self._resize_to_content()
    
    def handle_keep_suggestion(self, suggestion_data):
        """Handle Keep button click - apply suggestion to editor."""
        try:
            inserted_start = None
            inserted_end = None
            
            if suggestion_data.get('old_start') and suggestion_data.get('old_end'):
                # Replace existing code
                old_start = suggestion_data['old_start']
                old_end = suggestion_data['old_end']
                self.sql_editor.editor.delete(old_start, old_end)
                text = self._compute_gapped_text(old_start, suggestion_data['new_code'])
                self.sql_editor.editor.insert(old_start, text)
                
                inserted_start = old_start
                inserted_end = self.sql_editor.editor.index(f"{old_start}+{len(text)}c")
            else:
                # Insert at cursor
                cursor_pos = self.sql_editor.editor.index(tk.INSERT)
                text = self._compute_gapped_text(cursor_pos, suggestion_data['new_code'])
                self.sql_editor.editor.insert(cursor_pos, text)
                
                inserted_start = cursor_pos
                inserted_end = self.sql_editor.editor.index(f"{cursor_pos}+{len(text)}c")
            
            # Store range for undo (no highlighting - just insert as regular query)
            if inserted_start and inserted_end:
                # Move cursor to end of inserted text
                self.sql_editor.editor.mark_set(tk.INSERT, inserted_end)
                self.sql_editor.editor.see(inserted_end)
                
                # Store range for undo functionality
                try:
                    self.sql_editor.editor.tag_remove("ai_last_insert", "1.0", tk.END)
                except Exception:
                    pass
                self.sql_editor.editor.tag_add("ai_last_insert", inserted_start, inserted_end)
                self._last_ai_insert_range = (inserted_start, inserted_end)
            
            # Add confirmation message with "Optimize Again" button
            self.add_confirmation_with_optimize_again(inserted_start, inserted_end, suggestion_data['new_code'])
            
            # Disable Keep/Reject buttons
            self.disable_suggestion_buttons(suggestion_data)
            
        except Exception as e:
            print(f"Error applying suggestion: {e}")
            self.add_confirmation_message(f"❌ Error applying suggestion: {str(e)}")

    def _compact_keep_action(self, suggestion_data, keep_btn_ref, discard_btn_ref, button_start_pos):
        """Handle Keep button click - remove buttons and show 'Query accepted' text."""
        try:
            # Remove buttons and replace with text
            try:
                # Destroy button widgets
                keep_btn_ref.destroy()
                discard_btn_ref.destroy()
                
                # Delete the button area and insert status text
                button_end_pos = self.chat_text.index(f"{button_start_pos}+1c")  # Approximate end
                # Try to find where buttons actually end
                try:
                    self.chat_text.config(state=tk.NORMAL)
                    # Find the end of button area by looking for the next newline
                    content = self._safe_chat_get(button_start_pos, f"{button_start_pos} lineend")
                    if "    " in content or "\n" in content:
                        # Buttons are on this line, replace up to newline
                        line_end = self.chat_text.index(f"{button_start_pos} lineend")
                        self.chat_text.delete(button_start_pos, line_end)
                    else:
                        # Fallback: delete a reasonable amount
                        self.chat_text.delete(button_start_pos, f"{button_start_pos}+50c")
                except Exception:
                    # Fallback: just delete a chunk
                    try:
                        self.chat_text.config(state=tk.NORMAL)
                        self.chat_text.delete(button_start_pos, f"{button_start_pos}+50c")
                    except Exception:
                        pass
                
                # Insert "Query accepted" text (no margin, use normal_text like other text)
                self.chat_text.insert(button_start_pos, "✅ Query accepted\n", "normal_text")
                self.chat_text.config(state=tk.DISABLED)
            except Exception as e:
                print(f"Error removing buttons: {e}")
            
            # Call the main handler
            self.handle_keep_suggestion(suggestion_data)
        except Exception as e:
            print(f"Error in keep action: {e}")
            # Fallback: just disable buttons if removal fails
            try:
                keep_btn_ref.config(text="Query accepted", state=tk.DISABLED, fg="#28a745", font=("Arial", 9))
                discard_btn_ref.config(state=tk.DISABLED)
            except Exception:
                pass

    def _compact_reject_action(self, suggestion_data, keep_btn_ref, discard_btn_ref, button_start_pos):
        """Handle reject action - remove buttons and show 'Query rejected' text."""
        try:
            # Remove buttons and replace with text
            try:
                # Destroy button widgets
                keep_btn_ref.destroy()
                discard_btn_ref.destroy()
                
                # Delete the button area and insert status text
                button_end_pos = self.chat_text.index(f"{button_start_pos}+1c")  # Approximate end
                # Try to find where buttons actually end
                try:
                    self.chat_text.config(state=tk.NORMAL)
                    # Find the end of button area by looking for the next newline
                    content = self._safe_chat_get(button_start_pos, f"{button_start_pos} lineend")
                    if "    " in content or "\n" in content:
                        # Buttons are on this line, replace up to newline
                        line_end = self.chat_text.index(f"{button_start_pos} lineend")
                        self.chat_text.delete(button_start_pos, line_end)
                    else:
                        # Fallback: delete a reasonable amount
                        self.chat_text.delete(button_start_pos, f"{button_start_pos}+50c")
                except Exception:
                    # Fallback: just delete a chunk
                    try:
                        self.chat_text.config(state=tk.NORMAL)
                        self.chat_text.delete(button_start_pos, f"{button_start_pos}+50c")
                    except Exception:
                        pass
                
                # Insert "Query rejected" text (no margin, use normal_text like other text)
                self.chat_text.insert(button_start_pos, "❌ Query rejected\n", "normal_text")
                self.chat_text.config(state=tk.DISABLED)
            except Exception as e:
                print(f"Error removing buttons: {e}")
            
            # Call the main handler
            self.handle_discard_suggestion(suggestion_data)
        except Exception as e:
            print(f"Error in reject action: {e}")
            # Fallback: just disable buttons if removal fails
            try:
                discard_btn_ref.config(text="Query rejected", state=tk.DISABLED, fg="#dc3545", font=("Arial", 9))
                keep_btn_ref.config(state=tk.DISABLED)
            except Exception:
                pass

    # Removed inline Insert/Undo bar per new compact UX
    
    def handle_discard_suggestion(self, suggestion_data):
        """Handle Discard button click - ignore suggestion."""
        # Remove any highlights from old code
        if suggestion_data.get('old_start') and suggestion_data.get('old_end'):
            self.remove_old_highlight(suggestion_data['old_start'], suggestion_data['old_end'])
        
        # Don't add discard message here - "Query rejected" is already shown by _compact_reject_action
        # This prevents duplicate messages
        
        # Disable buttons
        self.disable_suggestion_buttons(suggestion_data)
    
    def disable_suggestion_buttons(self, suggestion_data):
        """Disable the Keep/Discard buttons after action."""
        try:
            # Match by comparing key fields that uniquely identify the suggestion
            for btn_id, btn_info in self.inline_buttons.items():
                stored_data = btn_info.get('data', {})
                # Compare by key fields (new_code is the most reliable identifier)
                if stored_data.get('new_code') == suggestion_data.get('new_code'):
                    # Additional checks to ensure it's the right suggestion (if available)
                    old_code_match = (stored_data.get('old_code') == suggestion_data.get('old_code'))
                    old_start_match = (stored_data.get('old_start') == suggestion_data.get('old_start'))
                    old_end_match = (stored_data.get('old_end') == suggestion_data.get('old_end'))
                    
                    # Match if new_code matches AND (all other fields match OR old_code fields are None/missing)
                    if (old_code_match and old_start_match and old_end_match) or \
                       (not suggestion_data.get('old_code') and not stored_data.get('old_code')):
                        try:
                            btn_info['keep'].config(state=tk.DISABLED)
                            btn_info['discard'].config(state=tk.DISABLED)
                        except Exception as e:
                            print(f"Error disabling button: {e}")
                        break
        except Exception as e:
            print(f"Error disabling buttons: {e}")
    
    def add_confirmation_message(self, message):
        """Add a confirmation message to chat."""
        self._safe_chat_insert(tk.END, f"{message}\n\n", "separator")
        try:
            self.chat_text.config(state=tk.NORMAL)
            self.chat_text.see(tk.END)
            self.chat_text.config(state=tk.DISABLED)
        except Exception:
            pass
    
    def add_confirmation_with_optimize_again(self, start_pos, end_pos, query_text):
        """Add confirmation message with Optimize Again button."""
        try:
            # Don't show "Query inserted" here - "Query accepted" is already shown by _compact_keep_action
            # Just add the "Optimize Again" button
            
            # Create "Optimize Again" button
            optimize_btn = tk.Button(self.chat_text,
                                    text="🔄 Optimize Again",
                                    bg="#1e1e1e", fg="#17a2b8", bd=0,
                                    font=("Arial", 9, "underline"),
                                    cursor="hand2",
                                    relief="flat", activebackground="#1e1e1e",
                                    activeforeground="#1fbad1", highlightthickness=0)
            
            # Bind command to optimize the inserted query
            def optimize_again():
                try:
                    # Get the query text from the inserted range
                    if start_pos and end_pos:
                        query = self.sql_editor.editor.get(start_pos, end_pos).strip()
                        if query:
                            # Pre-fill the input with optimization request
                            self.input_var.set(f"Optimize and improve this query:\n\n{query}")
                            # Focus input
                            self.input_entry.focus()
                            # Trigger generation
                            self.generate_sql()
                    else:
                        # Fallback: use the query text passed to this function
                        self.input_var.set(f"Optimize and improve this query:\n\n{query_text}")
                        self.input_entry.focus()
                        self.generate_sql()
                except Exception as e:
                    print(f"Error in optimize_again: {e}")
            
            optimize_btn.configure(command=optimize_again)
            
            # Insert button inline (no spacing before - align to margin like other text)
            try:
                self.chat_text.config(state=tk.NORMAL)
                self.chat_text.insert(tk.END, " ", "normal_text")  # Just a single space
                self.chat_text.window_create(tk.END, window=optimize_btn)
                self.chat_text.insert(tk.END, "\n", "normal_text")
                self.chat_text.see(tk.END)
                self.chat_text.config(state=tk.DISABLED)
            except Exception as e:
                print(f"Error inserting optimize button: {e}")
                try:
                    self.chat_text.config(state=tk.DISABLED)
                except:
                    pass
        except Exception as e:
            print(f"Error adding optimize again button: {e}")
            # Don't show duplicate message on error - "Query accepted" is already shown
    
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
        """Highlight applied code in green (legacy method, kept for compatibility)."""
        try:
            # Use the new persistent green highlight
            self.sql_editor.editor.tag_configure("ai_accepted", 
                                                background="#4CAF50",  # Bright green
                                                foreground="#000000",
                                                relief="flat",
                                                borderwidth=0)
            self.sql_editor.editor.tag_add("ai_accepted", start_pos, end_pos)
            
            # Also add manual highlight for easy re-optimization
            if hasattr(self.sql_editor.editor, 'tag_configure'):
                # Ensure manual_highlight tag exists
                try:
                    self.sql_editor.editor.tag_configure("manual_highlight", 
                                                        background="#ffeb3b",
                                                        foreground="#000000")
                except:
                    pass
                self.sql_editor.editor.tag_add("manual_highlight", start_pos, end_pos)
            
            # Don't auto-remove - let user control when to remove
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
        
        # Clear button removed - users cannot clear the modal
        
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
            
    def get_highlighted_text_from_editor(self):
        """Get manually highlighted text (Ctrl+/) from the SQL editor."""
        try:
            if hasattr(self.sql_editor, 'editor'):
                # Check for manual highlight tag
                highlight_ranges = self.sql_editor.editor.tag_ranges("manual_highlight")
                
                if highlight_ranges:
                    # Extract all highlighted text segments and combine them
                    highlighted_segments = []
                    for i in range(0, len(highlight_ranges), 2):
                        start = self.sql_editor.editor.index(highlight_ranges[i])
                        end = self.sql_editor.editor.index(highlight_ranges[i + 1])
                        segment = self.sql_editor.editor.get(start, end)
                        if segment.strip():
                            highlighted_segments.append(segment.strip())
                    
                    if highlighted_segments:
                        # Combine all highlighted segments with newlines
                        combined_text = "\n".join(highlighted_segments)
                        return combined_text
        except Exception as e:
            print(f"Error getting highlighted text: {e}")
        return None
    
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
        
        # Add user message to session context BEFORE processing
        if prompt:
            self.session_context.append({'role': 'user', 'content': prompt})
            if len(self.session_context) > self._max_context_items:
                self.session_context = self.session_context[-self._max_context_items:]
        
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
                    instruction = f"""Complete the following partial SQL query into a valid, executable SQLite query.
The user has selected this partial query and wants you to complete it:

{seltext}

Please complete the query using the database schema and ensure it's syntactically correct and executable."""
                    
                    ai_prompt = self._build_enhanced_prompt(
                        user_request=instruction,
                        include_schema=True,
                        include_history=True,
                        include_highlighted_query=False  # Already in instruction
                    )
                    
                    schema = self._get_formatted_schema()
                    ai_sql = None
                    self.ai_response_pending = True
                    # Add user message to chat first
                    self.add_chat_message("user", f"Complete partial SQL: {seltext[:100]}..." if len(seltext) > 100 else f"Complete partial SQL: {seltext}")
                    
                    try:
                        self._debug_print_prompt(ai_prompt)
                        ai_sql = self.ai_integration.generate_sql_query(ai_prompt, schema)
                    except Exception as e:
                        self._handle_ai_error(e)
                        ai_sql = None  # Ensure ai_sql is None on error
                    finally:
                        self.ai_response_pending = False
                    
                    if ai_sql is None:  # Error occurred
                        self.input_entry.configure(state="normal")
                        self.input_var.set("")
                        return
                    
                    if not ai_sql or not str(ai_sql).strip():
                        self._warn_once("⚠️ No response generated. Try rephrasing your query.")
                        self.input_entry.configure(state="normal")
                        self.input_var.set("")
                        return
                    # Parse AI response to extract explanation and SQL
                    parsed = self._parse_ai_response(ai_sql)
                    ai_sql_clean = parsed['sql']
                    explanation = parsed.get('explanation')
                    
                    if not self._looks_like_sql(ai_sql_clean):
                        self._warn_once("⚠️ No SQL query detected. Try rephrasing your prompt.")
                        self.input_entry.configure(state="normal")
                        self.input_var.set("")
                        return
                    # Add suggestion with NEW only (no OLD) and explanation
                    self._add_suggestion_block("", ai_sql_clean, explanation=explanation)
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
                instruction = f"""The user has selected the following SQL query and wants you to improve, fix, or optimize it:

{seltext}

Please provide an improved version of this query. Consider:
- Fixing any syntax errors
- Optimizing performance
- Improving readability
- Adding proper error handling if applicable
- Using best SQL practices"""
                
                ai_prompt = self._build_enhanced_prompt(
                    user_request=instruction,
                    include_schema=True,
                    include_history=True,
                    include_highlighted_query=False  # Already in instruction
                )
                
                schema = self._get_formatted_schema()
                # Call AI
                ai_sql = None
                self.ai_response_pending = True
                # Show user message first
                self.add_chat_message("user", prompt if prompt else f"Improve query: {seltext[:100]}..." if len(seltext) > 100 else f"Improve query: {seltext}")
                
                try:
                    self._debug_print_prompt(ai_prompt)
                    ai_sql = self.ai_integration.generate_sql_query(ai_prompt, schema)
                except Exception as e:
                    self._handle_ai_error(e)
                    ai_sql = None  # Ensure ai_sql is None on error
                finally:
                    self.ai_response_pending = False
                
                if ai_sql is None:  # Error occurred, skip rest
                    self.input_entry.configure(state="normal")
                    self.input_var.set("")
                    return
                
                # Handle empty/missing response
                if not ai_sql or not str(ai_sql).strip():
                    self._warn_once("⚠️ No response generated. Try rephrasing your query.")
                    self.input_entry.configure(state="normal")
                    self.input_var.set("")
                    return
                # Parse AI response to extract explanation and SQL
                parsed = self._parse_ai_response(ai_sql)
                ai_sql_clean = parsed['sql']
                explanation = parsed.get('explanation')
                
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
                # Determine selection positions (best-effort)
                sel_start, sel_end = None, None
                try:
                    sel_start = self.sql_editor.editor.index(tk.SEL_FIRST)
                    sel_end = self.sql_editor.editor.index(tk.SEL_LAST)
                except Exception:
                    pass
                # Show suggestion block with explanation
                self._add_suggestion_block(seltext, ai_sql_clean, sel_start, sel_end, explanation=explanation)
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
                instruction = """Generate a relevant starter SQL query for this database. 
Based on the database schema, suggest a useful query that demonstrates the database structure.
This could be a simple SELECT query that shows data from one or more tables."""
                
                ai_prompt = self._build_enhanced_prompt(
                    user_request=instruction,
                    include_schema=True,
                    include_history=False,  # New query, no history needed
                    include_highlighted_query=True
                )
                
                schema = self._get_formatted_schema()
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
                # Parse AI response to extract explanation and SQL
                parsed = self._parse_ai_response(ai_sql)
                ai_sql_clean = parsed['sql']
                explanation = parsed.get('explanation')
                
                if not self._looks_like_sql(ai_sql_clean):
                    self._warn_once("⚠️ No SQL query detected. Try rephrasing your prompt.")
                    self.input_entry.configure(state="normal")
                    self.input_var.set("")
                    return
                # Show user and assistant messages
                self.add_chat_message("user", "Generate starter SQL query")
                # Use _add_suggestion_block with explanation
                try:
                    self._add_suggestion_block("", ai_sql_clean, explanation=explanation)
                except Exception:
                    pass
                self.input_entry.configure(state="normal")
                self.input_var.set("")
                if hasattr(self, 'chat_text'):
                    self.chat_text.see('end')
                return
            # If non-SQL prompt, convert natural language to SQL (use full file as context too)
            if not self._looks_like_sql(prompt_text):
                norm_instruction = self._normalize_mentions(prompt_text)
                instruction = f"""The user has provided a natural language request to generate or modify SQL.
Please convert this request into a valid SQL query.

User Request (with normalized mentions): {norm_instruction}

Generate a complete, executable SQL query that fulfills the user's request."""
                
                ai_prompt = self._build_enhanced_prompt(
                    user_request=instruction,
                    include_schema=True,
                    include_history=True,
                    include_highlighted_query=True
                )
                
                # Add user message to chat first
                self.add_chat_message("user", prompt_text)
                
                schema = self._get_formatted_schema()
                ai_sql = None
                self.ai_response_pending = True
                try:
                    self._debug_print_prompt(ai_prompt)
                    ai_sql = self.ai_integration.generate_sql_query(ai_prompt, schema)
                except Exception as e:
                    self._handle_ai_error(e)
                    ai_sql = None  # Ensure ai_sql is None on error
                finally:
                    self.ai_response_pending = False
                
                if ai_sql is None:  # Error occurred
                    self.input_entry.configure(state="normal")
                    self.input_var.set("")
                    return
                
                if not ai_sql or not str(ai_sql).strip():
                    self._warn_once("⚠️ No response generated. Try rephrasing your query.")
                    self.input_entry.configure(state="normal")
                    self.input_var.set("")
                    return
                # Parse AI response to extract explanation and SQL
                parsed = self._parse_ai_response(ai_sql)
                ai_sql_clean = parsed['sql']
                explanation = parsed.get('explanation')
                
                # Use _add_suggestion_block directly - it will show the assistant message with suggestion
                try:
                    self._add_suggestion_block("", ai_sql_clean, explanation=explanation)
                except Exception:
                    pass
                self.input_entry.configure(state="normal")
                self.input_var.set("")
                if hasattr(self, 'chat_text'):
                    self.chat_text.see('end')
                return
            # Otherwise, treat as direct SQL text and refine
            norm_request = self._normalize_mentions(prompt_text)
            instruction = f"""The user has provided what appears to be SQL or a SQL-related request: {norm_request}

Please generate a complete, executable SQL query. If the input is already valid SQL, you may optimize or refine it.
Otherwise, interpret the request and generate appropriate SQL."""
            
            ai_prompt = self._build_enhanced_prompt(
                user_request=instruction,
                include_schema=True,
                include_history=True,
                include_highlighted_query=True
            )
            
            # Add user message to chat first
            self.add_chat_message("user", prompt_text)
            
            schema = self._get_formatted_schema()
            ai_sql = None
            self.ai_response_pending = True
            try:
                self._debug_print_prompt(ai_prompt)
                ai_sql = self.ai_integration.generate_sql_query(ai_prompt, schema)
            except Exception as e:
                self._handle_ai_error(e)
                ai_sql = None  # Ensure ai_sql is None on error
            finally:
                self.ai_response_pending = False
            # Error occurred, skip rest of processing
            if ai_sql is None:
                self.input_entry.configure(state="normal")
                self.input_var.set("")
                return
            if not ai_sql or not str(ai_sql).strip():
                self._warn_once("⚠️ No response generated. Try rephrasing your query.")
                self.input_entry.configure(state="normal")
                self.input_var.set("")
                return
            # Parse AI response to extract explanation and SQL
            parsed = self._parse_ai_response(ai_sql)
            ai_sql_clean = parsed['sql']
            explanation = parsed.get('explanation')
            
            if not self._looks_like_sql(ai_sql_clean):
                self._warn_once("⚠️ No SQL query detected. Try rephrasing your prompt.")
                self.input_entry.configure(state="normal")
                self.input_var.set("")
                return
            # Plain generated SQL: show user message and assistant response with suggestion block
            self.add_chat_message("user", prompt_text)
            # Use _add_suggestion_block directly - it will show the assistant message with suggestion
            try:
                self._add_suggestion_block("", ai_sql_clean, explanation=explanation)
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
            # Do not auto-remove ai_prompt or ai_accepted; they're persistent until user drops them
        except Exception as e:
            print(f"Error removing highlights: {e}")
    
    def remove_accepted_highlight(self):
        """Remove the green accepted highlight (call this when user edits the query)."""
        try:
            self.sql_editor.editor.tag_remove("ai_accepted", "1.0", tk.END)
        except Exception as e:
            print(f"Error removing accepted highlight: {e}")
    
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
        """Hide the modal without clearing conversation history."""
        if not self.is_visible or not self.modal_window:
            return
            
        self.is_visible = False
        self.chat_expanded = False
        
        # DO NOT clear conversation history - preserve it for next time
        # self.conversation_history = []  # Preserved
        # self.chat_messages = []  # Preserved
        # self.suggestion_buttons = {}  # Preserved
        # self.inline_buttons = {}  # Preserved
        # self.session_context = []  # Preserved
        
        # DO NOT clear chat text - preserve it
        # if hasattr(self, 'chat_text'):
        #     self.chat_text.delete("1.0", tk.END)  # Preserved
        
        # Remove all highlights (this is safe)
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

    def _parse_ai_response(self, ai_response):
        """Parse AI response to extract explanation and SQL query.
        
        Returns a dict with 'explanation' and 'sql' keys.
        """
        if not isinstance(ai_response, str):
            return {'explanation': None, 'sql': str(ai_response) if ai_response else ''}
        
        text = ai_response.strip()
        if not text:
            return {'explanation': None, 'sql': ''}
        
        explanation = None
        sql = None
        
        # Try to parse structured format: EXPLANATION: ... SQL_QUERY: ...
        # Check for explanation markers (case-insensitive)
        text_upper = text.upper()
        if "EXPLANATION:" in text_upper:
            # Find explanation section (try multiple case variations)
            exp_markers = ["EXPLANATION:", "Explanation:", "explanation:", "EXPLANATION", "Explanation", "explanation"]
            sql_markers = ["SQL_QUERY:", "SQL_QUERY", "sql_query:", "SQL:", "Sql:", "sql:", "QUERY:", "Query:", "query:"]
            
            for exp_marker in exp_markers:
                # Try case-insensitive search
                exp_pos = text_upper.find(exp_marker.upper())
                if exp_pos != -1:
                    # Also check exact case match for better extraction
                    if exp_marker in text:
                        exp_start = text.find(exp_marker) + len(exp_marker)
                    else:
                        exp_start = exp_pos + len(exp_marker)
                    
                    # Find where SQL section starts
                    sql_start_pos = len(text)
                    remaining_text_upper = text_upper[exp_start:]
                    for sql_marker in sql_markers:
                        sql_pos_upper = remaining_text_upper.find(sql_marker.upper())
                        if sql_pos_upper != -1:
                            sql_pos = text.find(sql_marker, exp_start)
                            if sql_pos != -1 and sql_pos < sql_start_pos:
                                sql_start_pos = sql_pos
                            # Also try case-insensitive position
                            elif sql_pos_upper != -1:
                                sql_pos_abs = exp_start + sql_pos_upper
                                if sql_pos_abs < sql_start_pos:
                                    sql_start_pos = sql_pos_abs
                    
                    explanation = text[exp_start:sql_start_pos].strip()
                    # Clean up explanation (remove leading/trailing dashes, colons, etc.)
                    explanation = explanation.strip(':- \n\r\t')
                    if explanation:
                        break
            
            # Find SQL section (case-insensitive)
            for sql_marker in sql_markers:
                sql_pos_upper = text_upper.find(sql_marker.upper())
                if sql_pos_upper != -1:
                    # Try exact case first
                    if sql_marker in text:
                        sql_start = text.find(sql_marker) + len(sql_marker)
                    else:
                        sql_start = sql_pos_upper + len(sql_marker)
                    sql = text[sql_start:].strip()
                    if sql:
                        break
        
        # If no structured format found, try to extract SQL from response
        if not sql:
            # Look for SQL keywords
            lines = text.split('\n')
            sql_lines = []
            found_sql = False
            explanation_lines = []
            for line in lines:
                line_upper = line.strip().upper()
                # Check if this line looks like SQL
                if any(line_upper.startswith(kw) for kw in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'WITH']):
                    found_sql = True
                    sql_lines.append(line)
                elif found_sql:
                    # Continue collecting SQL lines
                    sql_lines.append(line)
                elif not found_sql and line.strip():
                    # Before SQL starts, this might be explanation text
                    # Skip markdown code fences and empty lines
                    line_clean = line.strip()
                    if (line_clean and 
                        not line_clean.startswith('```') and 
                        not line_clean.startswith('EXPLANATION') and
                        not any(line_clean.upper().startswith(kw) for kw in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER'])):
                        explanation_lines.append(line_clean)
            
            # Combine explanation lines if we found any
            if explanation_lines and not explanation:
                explanation = ' '.join(explanation_lines).strip()
            
            if sql_lines:
                sql = '\n'.join(sql_lines)
        
        # Clean SQL
        if sql:
            sql = self._clean_sql_display(sql)
        
        # If still no explanation but we have text before SQL, use that
        if not explanation and sql:
            sql_start_in_text = text.find(sql[:min(50, len(sql))]) if sql else -1
            if sql_start_in_text > 0:
                potential_explanation = text[:sql_start_in_text].strip()
                # Remove common markers and clean up
                potential_explanation = potential_explanation.replace('EXPLANATION:', '').replace('explanation:', '').strip()
                if potential_explanation and len(potential_explanation) > 10:  # Only use if substantial
                    explanation = potential_explanation
        
        # Return results
        return {
            'explanation': explanation if explanation and explanation.strip() else None,
            'sql': sql or text  # Fallback to full text if no SQL extracted
        }
    
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
            # Temporarily enable to get metrics
            self.chat_text.config(state=tk.NORMAL)
            # Prefer precise pixel count for full content height
            total_pixels = 0
            try:
                total_pixels = int(self.chat_text.count("1.0", "end", "ypixels")[0])
            except Exception:
                # Fallback to last line metrics if count unsupported
                info = self.chat_text.dlineinfo("end-1c")
                if not info:
                    self.chat_text.config(state=tk.DISABLED)
                    return
                _, y, _, h, _, _ = info
                total_pixels = y + h + 6
            self.chat_text.config(state=tk.DISABLED)
            current_height = self.modal_window.winfo_height()
            extra = max(total_pixels, self._min_chat_extra_px)
            target_extra = min(extra, self._max_chat_extra_px)
            target_height = self._base_modal_height + target_extra
            if abs(current_height - target_height) > 4:
                self.modal_window.after_idle(lambda: self.modal_window.wm_geometry(f"{self.modal_width}x{target_height}"))
        except Exception:
            try:
                self.chat_text.config(state=tk.DISABLED)
            except:
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
    
    def _get_formatted_schema(self) -> Dict[str, Any]:
        """Get properly formatted database schema with full table and column information."""
        try:
            if not self.db_manager or not self.db_manager.current_db:
                return None
            
            # Use the proper schema extraction method if available
            if hasattr(self.db_manager, 'get_database_schema_for_ai'):
                return self.db_manager.get_database_schema_for_ai()
            
            # Fallback: manual extraction
            tables = self.db_manager.get_tables()
            schema = {
                "database_name": self.db_manager.current_db,
                "tables": [],
                "relationships": []
            }
            
            for table_name in tables:
                try:
                    # Get column info using PRAGMA
                    self.db_manager.cursor.execute(f"PRAGMA table_info({table_name})")
                    columns_info = self.db_manager.cursor.fetchall()
                    
                    columns = []
                    for col in columns_info:
                        # PRAGMA table_info returns: (cid, name, type, notnull, dflt_value, pk)
                        col_info = {
                            "name": col[1],
                            "type": col[2],
                            "nullable": not bool(col[3]),
                            "primary_key": bool(col[5]),
                            "default_value": col[4] if col[4] is not None else None
                        }
                        columns.append(col_info)
                    
                    table_info = {
                        "table_name": table_name,
                        "columns": columns
                    }
                    schema["tables"].append(table_info)
                    
                    # Get foreign key relationships
                    self.db_manager.cursor.execute(f"PRAGMA foreign_key_list({table_name})")
                    foreign_keys = self.db_manager.cursor.fetchall()
                    
                    for fk in foreign_keys:
                        # PRAGMA foreign_key_list returns: (id, seq, table, from, to, on_update, on_delete, match)
                        relationship = {
                            "from_table": table_name,
                            "from_column": fk[3],
                            "to_table": fk[2],
                            "to_column": fk[4]
                        }
                        schema["relationships"].append(relationship)
                        
                except Exception as e:
                    print(f"Error extracting schema for table {table_name}: {e}")
                    continue
            
            return schema
        except Exception as e:
            print(f"Error getting formatted schema: {e}")
            return None
    
    def _format_schema_for_prompt(self, schema: Dict[str, Any]) -> str:
        """Format database schema in a clean, readable format for AI prompts."""
        if not schema or not schema.get('tables'):
            return "DATABASE SCHEMA: No database schema available.\n"
        
        db_name = schema.get('database_name', 'Unknown')
        formatted = f"""
═══════════════════════════════════════════════════════════════
DATABASE SCHEMA
═══════════════════════════════════════════════════════════════
Database: {db_name}

"""
        
        # Format each table
        for table in schema.get('tables', []):
            table_name = table.get('table_name', 'unknown')
            columns = table.get('columns', [])
            
            formatted += f"📊 TABLE: {table_name}\n"
            formatted += "   Columns:\n"
            
            for col in columns:
                col_name = col.get('name', 'unknown')
                col_type = col.get('type', 'TEXT')
                is_pk = col.get('primary_key', False)
                is_nullable = col.get('nullable', True)
                default_val = col.get('default_value')
                
                # Build column description
                col_desc = f"      • {col_name} ({col_type})"
                
                if is_pk:
                    col_desc += " [PRIMARY KEY]"
                if not is_nullable:
                    col_desc += " [NOT NULL]"
                if default_val is not None:
                    col_desc += f" [DEFAULT: {default_val}]"
                
                formatted += col_desc + "\n"
            
            formatted += "\n"
        
        # Format relationships
        relationships = schema.get('relationships', [])
        if relationships:
            formatted += "🔗 RELATIONSHIPS (Foreign Keys):\n"
            for rel in relationships:
                from_tbl = rel.get('from_table', '')
                from_col = rel.get('from_column', '')
                to_tbl = rel.get('to_table', '')
                to_col = rel.get('to_column', '')
                formatted += f"   • {from_tbl}.{from_col} → {to_tbl}.{to_col}\n"
            formatted += "\n"
        
        formatted += "═══════════════════════════════════════════════════════════════\n"
        return formatted
    
    def _get_highlighted_query_for_prompt(self) -> str:
        """Get highlighted query text formatted for AI prompt."""
        try:
            if hasattr(self.sql_editor, 'get_query_for_ai'):
                query_text, is_highlighted = self.sql_editor.get_query_for_ai()
                if query_text and query_text.strip():
                    if is_highlighted:
                        return f"""
═══════════════════════════════════════════════════════════════
HIGHLIGHTED QUERY (User wants help with this specific query)
═══════════════════════════════════════════════════════════════
{query_text}

═══════════════════════════════════════════════════════════════
"""
                    else:
                        return f"""
═══════════════════════════════════════════════════════════════
CURRENT QUERY IN EDITOR (Full editor content)
═══════════════════════════════════════════════════════════════
{query_text}

═══════════════════════════════════════════════════════════════
"""
        except Exception as e:
            print(f"Error getting highlighted query: {e}")
        
        return ""
    
    def _format_conversation_history(self) -> str:
        """Format conversation history for AI prompt."""
        try:
            if not self.session_context or len(self.session_context) == 0:
                return ""
            
            history_text = """
═══════════════════════════════════════════════════════════════
CONVERSATION HISTORY
═══════════════════════════════════════════════════════════════
This is the context from previous interactions in this session.

"""
            
            # Include last N messages (most recent first, but we'll reverse for chronological order)
            recent_context = self.session_context[-self._max_context_items:]
            
            for idx, item in enumerate(recent_context, 1):
                role = item.get('role', 'user')
                content = (item.get('content') or '').strip()
                if not content:
                    continue
                
                role_label = "👤 USER" if role == 'user' else "🤖 ASSISTANT"
                # Truncate very long messages to avoid token bloat
                if len(content) > 2000:
                    content = content[:2000] + "\n... (truncated)"
                
                history_text += f"{idx}. {role_label}:\n{content}\n\n"
            
            history_text += "═══════════════════════════════════════════════════════════════\n"
            return history_text
        except Exception:
            return ""
    
    def _build_enhanced_prompt(self, user_request: str, include_schema: bool = True, 
                               include_history: bool = True, include_highlighted_query: bool = True,
                               instruction_context: str = "") -> str:
        """Build a comprehensive, well-structured prompt with all context."""
        
        prompt_parts = []
        
        # 1. Clear instruction header
        prompt_parts.append("""
═══════════════════════════════════════════════════════════════
INSTRUCTIONS
═══════════════════════════════════════════════════════════════
You are an expert SQL query assistant. Your task is to help generate, 
optimize, fix, or improve SQL queries for SQLite databases.

IMPORTANT GUIDELINES:
1. Generate clean, efficient, and valid SQLite-compatible SQL queries
2. Use proper SQL syntax and best practices
3. Include appropriate JOINs when working with multiple tables
4. Use WHERE clauses effectively for filtering
5. Consider performance implications
6. Return your response in the following format:
   EXPLANATION: [Brief English explanation of why this query is appropriate - what it does and why we're using it]
   SQL_QUERY: [The actual SQL query]
7. Ensure queries end with a semicolon (;)
8. If the user has highlighted specific query text, focus on that query
9. Use the provided database schema to ensure accurate table and column names
10. Consider conversation history for context in follow-up requests

═══════════════════════════════════════════════════════════════

""")
        
        # 2. Database Schema
        if include_schema:
            schema = self._get_formatted_schema()
            if schema:
                prompt_parts.append(self._format_schema_for_prompt(schema))
            else:
                prompt_parts.append("DATABASE SCHEMA: No database available.\n\n")
        
        # 3. Highlighted/Current Query
        if include_highlighted_query:
            highlighted_query = self._get_highlighted_query_for_prompt()
            if highlighted_query:
                prompt_parts.append(highlighted_query)
        
        # 4. Conversation History
        if include_history:
            history = self._format_conversation_history()
            if history:
                prompt_parts.append(history)
        
        # 5. Additional Context (ER, mentions, file context, etc.)
        context_parts = []
        
        er_text = self._get_er_text()
        if er_text:
            context_parts.append(er_text)
        
        mentions_text = self._get_mentions_text()
        if mentions_text:
            context_parts.append(mentions_text)
        
        convention = self._get_mention_convention_text()
        if convention:
            context_parts.append(convention)
        
        file_ctx = self._get_file_context_snippet()
        if file_ctx:
            context_parts.append(file_ctx)
        
        if context_parts:
            prompt_parts.append("""
═══════════════════════════════════════════════════════════════
ADDITIONAL CONTEXT
═══════════════════════════════════════════════════════════════
""")
            prompt_parts.append("\n".join(context_parts))
            prompt_parts.append("\n═══════════════════════════════════════════════════════════════\n")
        
        # 6. Custom instruction context (if provided)
        if instruction_context:
            prompt_parts.append(f"""
═══════════════════════════════════════════════════════════════
SPECIFIC INSTRUCTION
═══════════════════════════════════════════════════════════════
{instruction_context}

═══════════════════════════════════════════════════════════════
""")
        
        # 7. User Request
        prompt_parts.append(f"""
═══════════════════════════════════════════════════════════════
USER REQUEST
═══════════════════════════════════════════════════════════════
{user_request}

═══════════════════════════════════════════════════════════════

Please generate the appropriate SQL query based on the above context and user request.

IMPORTANT: Return your response in this exact format:
EXPLANATION: [A clear English explanation (3-4 lines) describing what this query does, why it's appropriate for the user's request, and what results it will produce. Make it informative and helpful.]
SQL_QUERY: [The actual SQL query without markdown or code fences]

The explanation is REQUIRED and helps the user understand the purpose and reasoning behind the query. Provide a detailed explanation in 3-4 lines.

""")
        
        return "\n".join(prompt_parts)

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

    def _add_suggestion_block(self, old_code, new_code, old_start=None, old_end=None, explanation=None):
        """Render a suggestion block using existing chat insertion. OLD may be empty."""
        try:
            suggestion_data = {
                'old_code': old_code if old_code else None,
                'new_code': new_code,
                'old_start': old_start,
                'old_end': old_end,
                'explanation': explanation
            }
            # Use assistant message with suggestion data (existing path)
            self.add_chat_message("assistant", "", suggestion_data)
        except Exception:
            pass
