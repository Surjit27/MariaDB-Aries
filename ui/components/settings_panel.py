import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox, simpledialog
from typing import Callable, Optional
from utils.settings_manager import SettingsManager

class SettingsPanel(ttk.Frame):
    """Settings panel with API key management and theme toggle."""
    
    def __init__(self, parent, settings_manager: SettingsManager, on_theme_changed: Callable = None, on_api_key_changed: Callable = None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.on_theme_changed = on_theme_changed
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

        # Theme Section
        self.create_theme_section(scrollable_frame)
        
        # API Keys Section
        self.create_api_keys_section(scrollable_frame)
        
        # General Settings Section
        self.create_general_section(scrollable_frame)
    
    def create_theme_section(self, parent):
        """Create theme selection section."""
        theme_frame = ttk.LabelFrame(parent, text="🎨 Theme", padding=10)
        theme_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Current theme display
        current_theme = self.settings_manager.get_theme()
        theme_label = ttk.Label(theme_frame, text=f"Current Theme: {current_theme.title()}", 
                               font=("Arial", 10))
        theme_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Theme selection buttons
        theme_buttons_frame = ttk.Frame(theme_frame)
        theme_buttons_frame.pack(fill=tk.X)
        
        # Dark theme button
        dark_btn = ttk.Button(theme_buttons_frame, text="🌙 Dark Mode", 
                             command=lambda: self.change_theme("darkly"))
        dark_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Light theme button
        light_btn = ttk.Button(theme_buttons_frame, text="☀️ Light Mode", 
                              command=lambda: self.change_theme("flatly"))
        light_btn.pack(side=tk.LEFT)
        
        # Highlight current theme
        if current_theme == "darkly":
            dark_btn.configure(style="Accent.TButton")
        else:
            light_btn.configure(style="Accent.TButton")
    
    def create_api_keys_section(self, parent):
        """Create API keys management section."""
        api_frame = ttk.LabelFrame(parent, text="🔑 API Keys (Gemini Only)", padding=10)
        api_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Add new API key button
        add_btn = ttk.Button(api_frame, text="➕ Add New API Key", 
                            command=self.add_api_key)
        add_btn.pack(anchor=tk.W, pady=(0, 10))
        
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
        self.api_tree.column("status", width=80)
        
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
    
    def change_theme(self, theme: str):
        """Change application theme."""
        if self.settings_manager.set_theme(theme):
            if self.on_theme_changed:
                self.on_theme_changed(theme)
            messagebox.showinfo("Success", f"Theme changed to {theme.title()}")
            # Refresh the theme section to highlight current theme
            self.refresh_theme_section()
        else:
            messagebox.showerror("Error", "Failed to change theme")
    
    def refresh_theme_section(self):
        """Refresh theme section to show current selection."""
        # This would require recreating the theme section or updating button styles
        pass
    
    def add_api_key(self):
        """Add a new API key."""
        dialog = APIKeyDialog(self, "Add New API Key")
        if dialog.result:
            name, api_key = dialog.result
            if self.settings_manager.add_api_key(name, api_key, "gemini"):
                self.refresh_api_keys()
                messagebox.showinfo("Success", f"API key '{name}' added successfully")
            else:
                messagebox.showerror("Error", "Failed to add API key. Name might already exist.")
    
    def edit_api_key(self):
        """Edit selected API key."""
        selection = self.api_tree.selection()
        if not selection:
            return
        
        item = self.api_tree.item(selection[0])
        key_id = item['values'][0]  # Assuming ID is in first column
        
        # Find the actual key data
        api_keys = self.settings_manager.get_api_keys()
        key_data = None
        for key in api_keys:
            if key['id'] == key_id:
                key_data = key
                break
        
        if key_data:
            dialog = APIKeyDialog(self, "Edit API Key", key_data['name'], key_data['api_key'])
            if dialog.result:
                new_name, new_key = dialog.result
                if self.settings_manager.update_api_key(key_id, new_name, new_key):
                    self.refresh_api_keys()
                    messagebox.showinfo("Success", "API key updated successfully")
                else:
                    messagebox.showerror("Error", "Failed to update API key")
    
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
        # Clear existing items
        for item in self.api_tree.get_children():
            self.api_tree.delete(item)
        
        # Add API keys
        api_keys = self.settings_manager.get_api_keys()
        selected_key = self.settings_manager.get_selected_api_key()
        
        for key in api_keys:
            status = "✅ Selected" if selected_key and key['id'] == selected_key['id'] else "⭕ Available"
            created_date = key.get('created_at', 'Unknown')[:10]  # Just the date part
            
            self.api_tree.insert("", tk.END, values=(
                key['name'],
                key.get('provider', 'gemini').title(),
                created_date,
                status
            ))
    
    def toggle_auto_save(self):
        """Toggle auto-save setting."""
        self.settings_manager.set_setting("auto_save", self.auto_save_var.get())
    
    def toggle_syntax_highlighting(self):
        """Toggle syntax highlighting setting."""
        self.settings_manager.set_setting("syntax_highlighting", self.syntax_var.get())
    
    def toggle_ai_autocomplete(self):
        """Toggle AI autocomplete setting."""
        self.settings_manager.set_setting("ai_autocomplete", self.ai_autocomplete_var.get())


class APIKeyDialog:
    """Dialog for adding/editing API keys."""
    
    def __init__(self, parent, title, name="", api_key=""):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x200")
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
        
        # API Key field
        ttk.Label(form_frame, text="Gemini API Key:").pack(anchor=tk.W, pady=(0, 5))
        self.api_key_var = tk.StringVar(value=api_key)
        api_key_entry = ttk.Entry(form_frame, textvariable=self.api_key_var, width=40, show="*")
        api_key_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Info label
        info_label = ttk.Label(form_frame, 
                              text="Note: Only Gemini API keys are supported. Get your key from Google AI Studio.",
                              font=("Arial", 8), foreground="gray")
        info_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Make Save button more prominent
        save_btn = ttk.Button(button_frame, text="💾 Save API Key", command=self.save, style="Accent.TButton")
        save_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        cancel_btn = ttk.Button(button_frame, text="❌ Cancel", command=self.cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Focus on name field
        name_entry.focus()
        
        # Bind Enter key to save
        self.dialog.bind("<Return>", lambda e: self.save())
        self.dialog.bind("<Escape>", lambda e: self.cancel())
    
    def save(self):
        """Save the API key."""
        name = self.name_var.get().strip()
        api_key = self.api_key_var.get().strip()
        
        if not name:
            messagebox.showerror("Error", "Please enter a name for the API key")
            return
        
        if not api_key:
            messagebox.showerror("Error", "Please enter the API key")
            return
        
        if len(api_key) < 20:
            messagebox.showerror("Error", "API key seems too short. Please check your input.")
            return
        
        if not api_key.startswith("AIza"):
            if not messagebox.askyesno("Warning", 
                                     "This doesn't look like a valid Gemini API key.\n\nValid Gemini API keys usually start with 'AIza'.\n\nContinue anyway?"):
                return
        
        self.result = (name, api_key)
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel the dialog."""
        self.dialog.destroy()
