import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox, simpledialog
from typing import Callable, Optional
from utils.settings_manager import SettingsManager

class SettingsPanel(ttk.Frame):
    """Settings panel with API key management."""
    
    def __init__(self, parent, settings_manager: SettingsManager, on_theme_changed: Callable = None, on_api_key_changed: Callable = None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.on_api_key_changed = on_api_key_changed
        self.create_widgets()
        self.refresh_api_keys()
    
    def create_widgets(self):
        """Create the settings UI."""
        # Main container with scrollbar
        main_canvas = tk.Canvas(self)
        main_scrollbar = ttk.Scrollbar(self, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")

        # Title
        title_label = ttk.Label(scrollable_frame, text="⚙️ Settings", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(10, 20))
        
        # API Keys Section
        self.create_api_keys_section(scrollable_frame)
        
        # General Settings Section
        self.create_general_section(scrollable_frame)
    
    def create_api_keys_section(self, parent):
        """Create API keys management section."""
        api_frame = ttk.LabelFrame(parent, text="🔑 API Keys (Gemini Only)", padding=10)
        api_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Add new API key button and refresh button
        btn_frame = ttk.Frame(api_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        add_btn = ttk.Button(btn_frame, text="➕ Add New API Key", 
                            command=self.add_api_key)
        add_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        refresh_btn = ttk.Button(btn_frame, text="🔄 Refresh List", 
                                command=self.refresh_api_keys)
        refresh_btn.pack(side=tk.LEFT)
        
        # API keys list
        list_frame = ttk.Frame(api_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for API keys
        columns = ("name", "provider", "created", "status")
        self.api_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=6)
        
        # Configure columns
        self.api_tree.heading("name", text="Name")
        self.api_tree.heading("provider", text="Provider")
        self.api_tree.heading("created", text="Created")
        self.api_tree.heading("status", text="Status")
        
        self.api_tree.column("name", width=150)
        self.api_tree.column("provider", width=80)
        self.api_tree.column("created", width=120)
        self.api_tree.column("status", width=120)  # Made wider for status
        
        # Configure tags for styling
        self.api_tree.tag_configure("selected", background="#e7f3ff")
        
        # Scrollbar for treeview
        tree_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.api_tree.yview)
        self.api_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.api_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.api_tree.bind("<<TreeviewSelect>>", self.on_api_key_selected)
        
        # Action buttons frame
        actions_frame = ttk.Frame(api_frame)
        actions_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.edit_btn = ttk.Button(actions_frame, text="✏️ Edit", 
                                  command=self.edit_api_key, state=tk.DISABLED)
        self.edit_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.delete_btn = ttk.Button(actions_frame, text="🗑️ Delete", 
                                    command=self.delete_api_key, state=tk.DISABLED)
        self.delete_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.select_btn = ttk.Button(actions_frame, text="✅ Select", 
                                    command=self.select_api_key, state=tk.DISABLED)
        self.select_btn.pack(side=tk.LEFT)
    
    def create_general_section(self, parent):
        """Create general settings section."""
        general_frame = ttk.LabelFrame(parent, text="⚙️ General Settings", padding=10)
        general_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Auto-save setting
        self.auto_save_var = tk.BooleanVar(value=self.settings_manager.get_setting("auto_save", True))
        auto_save_cb = ttk.Checkbutton(general_frame, text="Auto-save settings", 
                                      variable=self.auto_save_var,
                                      command=self.toggle_auto_save)
        auto_save_cb.pack(anchor=tk.W, pady=2)
        
        # Syntax highlighting setting
        self.syntax_var = tk.BooleanVar(value=self.settings_manager.get_setting("syntax_highlighting", True))
        syntax_cb = ttk.Checkbutton(general_frame, text="Enable syntax highlighting", 
                                   variable=self.syntax_var,
                                   command=self.toggle_syntax_highlighting)
        syntax_cb.pack(anchor=tk.W, pady=2)
        
        # AI autocomplete setting
        self.ai_autocomplete_var = tk.BooleanVar(value=self.settings_manager.get_setting("ai_autocomplete", True))
        ai_cb = ttk.Checkbutton(general_frame, text="Enable AI autocomplete", 
                               variable=self.ai_autocomplete_var,
                               command=self.toggle_ai_autocomplete)
        ai_cb.pack(anchor=tk.W, pady=2)
    
    def add_api_key(self):
        """Add a new API key with explicit save confirmation."""
        print("DEBUG: add_api_key() method called")
        dialog = APIKeyDialog(self, "Add New API Key")
        print(f"DEBUG: Dialog closed. Result: {dialog.result}")
        
        if dialog.result:
            name, api_key = dialog.result
            print(f"DEBUG: Attempting to add API key with name '{name}', key length={len(api_key)}")
            
            # Check current state before adding
            current_keys = self.settings_manager.get_api_keys()
            print(f"DEBUG: Current keys before add: {len(current_keys)}")
            print(f"DEBUG: Settings manager settings api_keys count: {len(self.settings_manager.settings.get('api_keys', []))}")
            
            # Attempt to save the API key (add_api_key already calls save_settings internally)
            success = self.settings_manager.add_api_key(name, api_key, "gemini")
            print(f"DEBUG: add_api_key returned: {success}")
            print(f"DEBUG: Settings after add (in memory): {len(self.settings_manager.settings.get('api_keys', []))}")
            
            if success:
                # Immediately check if it's in memory
                in_memory = len(self.settings_manager.settings.get('api_keys', []))
                print(f"DEBUG: Keys in memory after add_api_key: {in_memory}")
                
                # Force reload settings from disk (with small delay to allow file write)
                self.after(100, lambda: self._reload_and_refresh())
                
                # Also refresh immediately (using in-memory data)
                self.refresh_api_keys()
                
                # Verify the key was added
                api_keys = self.settings_manager.get_api_keys()
                found = any(k.get('name') == name for k in api_keys)
                print(f"DEBUG: Key verification - found in list: {found}")
                
                if found:
                    messagebox.showinfo("Success", 
                                      f"✅ API key '{name}' saved successfully!\n\n"
                                      f"The key has been stored and can be used now.\n"
                                      f"You can edit or replace it anytime from Settings.")
                    
                    # Trigger callback if API key changed
                    if self.on_api_key_changed:
                        self.on_api_key_changed()
                else:
                    error_msg = (f"⚠️ API key '{name}' was saved but not found in the list.\n\n"
                               f"In-memory count: {in_memory}\n"
                               f"Reloaded count: {reloaded_count}\n"
                               f"Please try refreshing or check the settings file manually.")
                    messagebox.showwarning("Warning", error_msg)
            else:
                messagebox.showerror("Error", 
                                    f"❌ Failed to add API key.\n\n"
                                    f"Reason: API key name '{name}' might already exist.\n"
                                    f"Please use a different name or edit the existing key.")
        else:
            print("DEBUG: Dialog result is None - user cancelled or validation failed")
    
    def edit_api_key(self):
        """Edit selected API key with explicit save confirmation."""
        selection = self.api_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an API key to edit.")
            return
        
        item = self.api_tree.item(selection[0])
        key_name = item['values'][0]  # Name is in first column
        
        # Reload settings to ensure we have the latest data
        self.settings_manager.settings = self.settings_manager.load_settings()
        
        # Find the actual key data by name (more reliable)
        api_keys = self.settings_manager.get_api_keys()
        key_data = None
        key_id = None
        for key in api_keys:
            if key.get('name') == key_name:
                key_data = key
                key_id = key.get('id')
                break
        
        if not key_data:
            messagebox.showerror("Error", f"Could not find API key '{key_name}' in settings.")
            self.refresh_api_keys()  # Refresh to sync
            return
        
        dialog = APIKeyDialog(self, "Edit API Key", key_data['name'], key_data['api_key'])
        if dialog.result:
            new_name, new_key = dialog.result
            
            # Attempt to update the API key (update_api_key already calls save_settings internally)
            if self.settings_manager.update_api_key(key_id, new_name, new_key):
                # Reload settings
                self.settings_manager.settings = self.settings_manager.load_settings()
                self.refresh_api_keys()
                
                messagebox.showinfo("Success", 
                                  f"✅ API key updated and saved successfully!\n\n"
                                  f"Name: {new_name}\n"
                                  f"The changes have been saved to disk.\n"
                                  f"You can replace or edit it again anytime.")
                
                # Trigger callback if API key changed
                if self.on_api_key_changed:
                    self.on_api_key_changed()
            else:
                messagebox.showerror("Error", 
                                   "❌ Failed to update API key.\n\n"
                                   "Please check your input and try again.")
    
    def delete_api_key(self):
        """Delete selected API key."""
        selection = self.api_tree.selection()
        if not selection:
            return
        
        item = self.api_tree.item(selection[0])
        key_name = item['values'][0]  # Name is in first column
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete API key '{key_name}'?"):
            # Find the key ID
            api_keys = self.settings_manager.get_api_keys()
            key_id = None
            for key in api_keys:
                if key['name'] == key_name:
                    key_id = key['id']
                    break
            
            if key_id and self.settings_manager.delete_api_key(key_id):
                self.refresh_api_keys()
                messagebox.showinfo("Success", "API key deleted successfully")
            else:
                messagebox.showerror("Error", "Failed to delete API key")
    
    def select_api_key(self):
        """Select the current API key."""
        selection = self.api_tree.selection()
        if not selection:
            return
        
        item = self.api_tree.item(selection[0])
        key_name = item['values'][0]  # Name is in first column
        
        # Find the key ID
        api_keys = self.settings_manager.get_api_keys()
        key_id = None
        for key in api_keys:
            if key['name'] == key_name:
                key_id = key['id']
                break
        
        if key_id and self.settings_manager.set_selected_api_key(key_id):
            self.refresh_api_keys()
            if self.on_api_key_changed:
                self.on_api_key_changed()
            messagebox.showinfo("Success", f"API key '{key_name}' selected")
        else:
            messagebox.showerror("Error", "Failed to select API key")
    
    def on_api_key_selected(self, event):
        """Handle API key selection in treeview."""
        selection = self.api_tree.selection()
        if selection:
            self.edit_btn.configure(state=tk.NORMAL)
            self.delete_btn.configure(state=tk.NORMAL)
            self.select_btn.configure(state=tk.NORMAL)
        else:
            self.edit_btn.configure(state=tk.DISABLED)
            self.delete_btn.configure(state=tk.DISABLED)
            self.select_btn.configure(state=tk.DISABLED)
    
    def refresh_api_keys(self):
        """Refresh the API keys list."""
        print("DEBUG: refresh_api_keys called")
        
        # Clear existing items
        for item in self.api_tree.get_children():
            self.api_tree.delete(item)
        
        # DON'T reload from disk every time - use in-memory settings which should be up-to-date
        # Only reload if we detect the in-memory is out of sync
        current_in_memory = len(self.settings_manager.settings.get('api_keys', []))
        print(f"DEBUG: In-memory api_keys count: {current_in_memory}")
        
        # If in-memory has keys, use it. Otherwise try reloading once.
        if current_in_memory == 0:
            print("DEBUG: In-memory is empty, attempting reload from disk")
            try:
                reloaded_settings = self.settings_manager.load_settings()
                reloaded_count = len(reloaded_settings.get('api_keys', []))
                print(f"DEBUG: Reloaded from disk. api_keys count: {reloaded_count}")
                
                if reloaded_count > 0:
                    # Only update if reloaded has more keys
                    self.settings_manager.settings = reloaded_settings
                    print(f"DEBUG: Updated in-memory with reloaded settings")
            except Exception as e:
                print(f"DEBUG: Error reloading settings: {e}")
        
        # Get fresh API keys list from current in-memory settings
        api_keys = self.settings_manager.get_api_keys()
        selected_key = self.settings_manager.get_selected_api_key()
        
        print(f"DEBUG: get_api_keys() returned {len(api_keys)} keys")
        if api_keys:
            # Only print first 50 chars of api_key to avoid debug spam
            first_key_sample = api_keys[0].copy()
            if 'api_key' in first_key_sample:
                api_key_val = first_key_sample['api_key']
                first_key_sample['api_key'] = api_key_val[:50] + '...' if len(api_key_val) > 50 else api_key_val
            print(f"DEBUG: First key sample: {first_key_sample}")
        
        # Add API keys to treeview
        for key in api_keys:
            # Get selected status
            key_id = key.get('id')
            selected_id = selected_key.get('id') if selected_key else None
            is_selected = key_id == selected_id
            status = "✅ Selected" if is_selected else "⭕ Available"
            
            # Format created date
            created_at = key.get('created_at', '')
            if created_at:
                try:
                    created_date = created_at[:10] if len(created_at) >= 10 else created_at
                except:
                    created_date = 'Unknown'
            else:
                created_date = 'Unknown'
            
            # Insert into treeview - store ID in item tags for reference
            item_id = self.api_tree.insert("", tk.END, values=(
                key.get('name', 'Unnamed'),
                key.get('provider', 'gemini').title(),
                created_date,
                status
            ), tags=(str(key_id),))  # Store ID in tags
            
            print(f"DEBUG: Inserted item '{key.get('name')}' with ID {key_id} into treeview")
        
        # Debug: verify treeview has items
        tree_items = self.api_tree.get_children()
        print(f"DEBUG: Treeview now has {len(tree_items)} items")
        
        # Force update the display
        self.api_tree.update_idletasks()
    
    def toggle_auto_save(self):
        """Toggle auto-save setting."""
        self.settings_manager.set_setting("auto_save", self.auto_save_var.get())
    
    def toggle_syntax_highlighting(self):
        """Toggle syntax highlighting setting."""
        self.settings_manager.set_setting("syntax_highlighting", self.syntax_var.get())
    
    def toggle_ai_autocomplete(self):
        """Toggle AI autocomplete setting."""
        self.settings_manager.set_setting("ai_autocomplete", self.ai_autocomplete_var.get())
    
    def _reload_and_refresh(self):
        """Helper method to reload settings and refresh the table."""
        print("DEBUG: _reload_and_refresh() called")
        self.settings_manager.settings = self.settings_manager.load_settings()
        reloaded_count = len(self.settings_manager.settings.get('api_keys', []))
        print(f"DEBUG: After reload, api_keys count: {reloaded_count}")
        self.refresh_api_keys()


class APIKeyDialog:
    """Dialog for adding/editing API keys."""
    
    def __init__(self, parent, title, name="", api_key=""):
        self.result = None
        self.dialog = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("450x220")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Create form
        form_frame = ttk.Frame(self.dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name field
        ttk.Label(form_frame, text="API Key Name:").pack(anchor=tk.W, pady=(0, 5))
        self.name_var = tk.StringVar(value=name)
        name_entry = ttk.Entry(form_frame, textvariable=self.name_var, width=40)
        name_entry.pack(fill=tk.X, pady=(0, 15))
        
        # API Key field - use Entry with StringVar (standard approach)
        ttk.Label(form_frame, text="Gemini API Key:").pack(anchor=tk.W, pady=(0, 5))
        self.api_key_var = tk.StringVar(value=api_key if api_key else "")
        self.api_key_entry = ttk.Entry(form_frame, textvariable=self.api_key_var, width=40, show="*")
        self.api_key_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Info label
        info_label = ttk.Label(form_frame, 
                              text="Note: Only Gemini API keys are supported. Get your key from Google AI Studio.",
                              font=("Arial", 8), foreground="gray")
        info_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Make Save button more prominent with clear label
        save_btn = ttk.Button(button_frame, text="💾 Save & Store API Key", command=self.save, style="Accent.TButton")
        save_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        cancel_btn = ttk.Button(button_frame, text="❌ Cancel", command=self.cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Focus on name field
        name_entry.focus()
        
        # Bind Enter key to save (only when in entry fields)
        name_entry.bind("<Return>", lambda e: self.save())
        self.api_key_entry.bind("<Return>", lambda e: self.save())
        self.api_key_entry.bind("<Control-v>", lambda e: None)  # Allow paste
        self.dialog.bind("<Escape>", lambda e: self.cancel())
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def save(self):
        """Save the API key with validation and explicit save confirmation."""
        name = self.name_var.get().strip()
        
        # Get API key from Entry widget's StringVar
        api_key = self.api_key_var.get().strip()
        
        print(f"DEBUG: APIKeyDialog.save() called with name='{name}', api_key length={len(api_key)}")
        print(f"DEBUG: API key preview (first 15 chars): '{api_key[:15] if len(api_key) > 15 else api_key}...'")
        
        if not name:
            messagebox.showerror("Error", "Please enter a name for the API key")
            return
        
        if not api_key:
            messagebox.showerror("Error", "Please enter the API key")
            return
        
        # Clean the API key - remove any newlines, carriage returns, or whitespace issues
        api_key = api_key.replace('\n', '').replace('\r', '').replace('\t', ' ').strip()
        
        # Additional check: remove any debug-like patterns
        if 'DEBUG:' in api_key or 'keysym=' in api_key or 'Text changed:' in api_key:
            messagebox.showerror("Error", 
                               "Invalid API key detected (contains debug text).\n\n"
                               "Please paste your API key again. Make sure you're copying only the key itself.")
            return
        
        if len(api_key) < 20:
            messagebox.showerror("Error", "API key seems too short. Please check your input.")
            return
        
        if not api_key.startswith("AIza"):
            response = messagebox.askyesno("Warning", 
                                     "This doesn't look like a valid Gemini API key.\n\nValid Gemini API keys usually start with 'AIza'.\n\nContinue anyway?")
            print(f"DEBUG: User response to AIza warning: {response}")
            if not response:
                return
        
        # Set result BEFORE closing dialog
        self.result = (name, api_key)
        print(f"DEBUG: APIKeyDialog - result set to: name='{name}', api_key starts with='{api_key[:10]}...' (length: {len(api_key)})")
        
        # Close dialog - parent will handle the actual save
        if self.dialog:
            self.dialog.destroy()
    
    def cancel(self):
        """Cancel the dialog."""
        self.dialog.destroy()
