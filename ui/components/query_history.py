import tkinter as tk
import ttkbootstrap as ttk
from datetime import datetime
from typing import List, Dict, Any, Callable

class QueryHistoryPanel(ttk.Frame):
    def __init__(self, parent, db_manager, on_query_selected: Callable = None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.on_query_selected = on_query_selected
        self.create_widgets()
        self.refresh_data()

    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Title
        title_label = ttk.Label(main_frame, text="Query History & Favorites", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))

        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # History tab
        self.history_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.history_frame, text="History")

        # History controls
        history_controls = ttk.Frame(self.history_frame)
        history_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(history_controls, text="Refresh", command=self.refresh_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(history_controls, text="Clear History", command=self.clear_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(history_controls, text="Export History", command=self.export_history).pack(side=tk.LEFT, padx=5)

        # History list
        history_list_frame = ttk.Frame(self.history_frame)
        history_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # History treeview
        self.history_tree = ttk.Treeview(history_list_frame, columns=("timestamp", "status", "database"), show="tree headings")
        self.history_tree.heading("#0", text="Query")
        self.history_tree.heading("timestamp", text="Time")
        self.history_tree.heading("status", text="Status")
        self.history_tree.heading("database", text="Database")
        
        self.history_tree.column("#0", width=300)
        self.history_tree.column("timestamp", width=120)
        self.history_tree.column("status", width=80)
        self.history_tree.column("database", width=100)

        # Scrollbar for history
        history_scrollbar = ttk.Scrollbar(history_list_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)

        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # History buttons
        history_buttons = ttk.Frame(self.history_frame)
        history_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(history_buttons, text="Use Query", command=self.use_history_query).pack(side=tk.LEFT, padx=5)
        ttk.Button(history_buttons, text="Copy Query", command=self.copy_history_query).pack(side=tk.LEFT, padx=5)
        ttk.Button(history_buttons, text="Add to Favorites", command=self.add_history_to_favorites).pack(side=tk.LEFT, padx=5)

        # Favorites tab
        self.favorites_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.favorites_frame, text="Favorites")

        # Favorites controls
        favorites_controls = ttk.Frame(self.favorites_frame)
        favorites_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(favorites_controls, text="Refresh", command=self.refresh_favorites).pack(side=tk.LEFT, padx=5)
        ttk.Button(favorites_controls, text="Add Current", command=self.add_current_to_favorites).pack(side=tk.LEFT, padx=5)

        # Favorites list
        favorites_list_frame = ttk.Frame(self.favorites_frame)
        favorites_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Favorites treeview
        self.favorites_tree = ttk.Treeview(favorites_list_frame, columns=("timestamp", "database"), show="tree headings")
        self.favorites_tree.heading("#0", text="Name")
        self.favorites_tree.heading("timestamp", text="Created")
        self.favorites_tree.heading("database", text="Database")
        
        self.favorites_tree.column("#0", width=200)
        self.favorites_tree.column("timestamp", width=120)
        self.favorites_tree.column("database", width=100)

        # Scrollbar for favorites
        favorites_scrollbar = ttk.Scrollbar(favorites_list_frame, orient=tk.VERTICAL, command=self.favorites_tree.yview)
        self.favorites_tree.configure(yscrollcommand=favorites_scrollbar.set)

        self.favorites_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        favorites_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Favorites buttons
        favorites_buttons = ttk.Frame(self.favorites_frame)
        favorites_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(favorites_buttons, text="Use Query", command=self.use_favorite_query).pack(side=tk.LEFT, padx=5)
        ttk.Button(favorites_buttons, text="Copy Query", command=self.copy_favorite_query).pack(side=tk.LEFT, padx=5)
        ttk.Button(favorites_buttons, text="Remove", command=self.remove_favorite).pack(side=tk.LEFT, padx=5)

        # Bind events
        self.history_tree.bind("<Double-1>", self.on_history_double_click)
        self.favorites_tree.bind("<Double-1>", self.on_favorite_double_click)

    def refresh_data(self):
        """Refresh both history and favorites."""
        self.refresh_history()
        self.refresh_favorites()

    def refresh_history(self):
        """Refresh query history."""
        self.history_tree.delete(*self.history_tree.get_children())
        history = self.db_manager.get_query_history()
        
        for item in reversed(history):  # Show newest first
            query_preview = item['query'][:50] + "..." if len(item['query']) > 50 else item['query']
            timestamp = item['timestamp'][:19] if 'timestamp' in item else "Unknown"
            status = item['status'][:20] if 'status' in item else "Unknown"
            database = item.get('database', 'Unknown')
            
            self.history_tree.insert("", tk.END, text=query_preview, 
                                   values=(timestamp, status, database))

    def refresh_favorites(self):
        """Refresh favorites list."""
        self.favorites_tree.delete(*self.favorites_tree.get_children())
        favorites = self.db_manager.get_favorites()
        
        for item in favorites:
            name = item.get('name', 'Unnamed')
            timestamp = item.get('timestamp', 'Unknown')[:19] if 'timestamp' in item else "Unknown"
            database = item.get('database', 'Unknown')
            
            self.favorites_tree.insert("", tk.END, text=name, 
                                     values=(timestamp, database))

    def clear_history(self):
        """Clear query history."""
        from tkinter import messagebox
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all query history?"):
            self.db_manager.query_history = []
            self.db_manager.save_query_history()
            self.refresh_history()

    def export_history(self):
        """Export query history to file."""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            import json
            with open(filename, 'w') as f:
                json.dump(self.db_manager.get_query_history(), f, indent=2)
            from tkinter import messagebox
            messagebox.showinfo("Success", f"History exported to {filename}")

    def use_history_query(self):
        """Use selected history query."""
        selection = self.history_tree.selection()
        if selection and self.on_query_selected:
            item = self.history_tree.item(selection[0])
            # Get full query from history
            history = self.db_manager.get_query_history()
            for hist_item in reversed(history):  # Match with reversed order
                query_preview = hist_item['query'][:50] + "..." if len(hist_item['query']) > 50 else hist_item['query']
                if item['text'] == query_preview:
                    self.on_query_selected(hist_item['query'])
                    break

    def copy_history_query(self):
        """Copy selected history query."""
        selection = self.history_tree.selection()
        if selection:
            item = self.history_tree.item(selection[0])
            # Get full query from history
            history = self.db_manager.get_query_history()
            for hist_item in reversed(history):
                query_preview = hist_item['query'][:50] + "..." if len(hist_item['query']) > 50 else hist_item['query']
                if item['text'] == query_preview:
                    self.clipboard_clear()
                    self.clipboard_append(hist_item['query'])
                    break

    def add_history_to_favorites(self):
        """Add selected history item to favorites."""
        selection = self.history_tree.selection()
        if selection:
            item = self.history_tree.item(selection[0])
            # Get full query from history
            history = self.db_manager.get_query_history()
            for hist_item in reversed(history):
                query_preview = hist_item['query'][:50] + "..." if len(hist_item['query']) > 50 else hist_item['query']
                if item['text'] == query_preview:
                    from tkinter import simpledialog
                    name = simpledialog.askstring("Add to Favorites", "Enter name for this query:")
                    if name:
                        self.db_manager.add_to_favorites(hist_item['query'], name)
                        self.refresh_favorites()
                    break

    def use_favorite_query(self):
        """Use selected favorite query."""
        selection = self.favorites_tree.selection()
        if selection and self.on_query_selected:
            item = self.favorites_tree.item(selection[0])
            name = item['text']
            # Get full query from favorites
            favorites = self.db_manager.get_favorites()
            for fav_item in favorites:
                if fav_item.get('name') == name:
                    self.on_query_selected(fav_item['query'])
                    break

    def copy_favorite_query(self):
        """Copy selected favorite query."""
        selection = self.favorites_tree.selection()
        if selection:
            item = self.favorites_tree.item(selection[0])
            name = item['text']
            # Get full query from favorites
            favorites = self.db_manager.get_favorites()
            for fav_item in favorites:
                if fav_item.get('name') == name:
                    self.clipboard_clear()
                    self.clipboard_append(fav_item['query'])
                    break

    def remove_favorite(self):
        """Remove selected favorite."""
        selection = self.favorites_tree.selection()
        if selection:
            item = self.favorites_tree.item(selection[0])
            name = item['text']
            # Remove from favorites
            favorites = self.db_manager.get_favorites()
            self.db_manager.favorites = [fav for fav in favorites if fav.get('name') != name]
            self.db_manager.save_favorites()
            self.refresh_favorites()

    def add_current_to_favorites(self):
        """Add current query to favorites."""
        from tkinter import simpledialog
        query = simpledialog.askstring("Add to Favorites", "Enter the query to save:")
        if query:
            name = simpledialog.askstring("Add to Favorites", "Enter name for this query:")
            if name:
                self.db_manager.add_to_favorites(query, name)
                self.refresh_favorites()

    def on_history_double_click(self, event):
        """Handle double-click on history item."""
        self.use_history_query()

    def on_favorite_double_click(self, event):
        """Handle double-click on favorite item."""
        self.use_favorite_query()
