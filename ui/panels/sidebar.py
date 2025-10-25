import tkinter as tk
import ttkbootstrap as ttk
from db.database_manager import DatabaseManager

class SidebarPanel(ttk.Frame):
    def __init__(self, parent, db_manager: DatabaseManager):
        super().__init__(parent)
        self.db_manager = db_manager
        self.create_widgets()
        self.refresh_databases()

    def create_widgets(self):
        # Filter bar (like SQLyog)
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(filter_frame, text="Filter tables:").pack(side=tk.LEFT)
        self.filter_entry = ttk.Entry(filter_frame, width=15)
        self.filter_entry.pack(side=tk.LEFT, padx=5)
        self.filter_entry.bind("<KeyRelease>", self.on_filter_change)
        
        # Treeview for database structure
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tree = ttk.Treeview(tree_frame, show="tree")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for tree
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind right-click for context menu
        self.tree.bind("<Button-3>", self.on_right_click)
        # Bind double-click to open database
        self.tree.bind("<Double-1>", self.on_double_click)

    def refresh_databases(self):
        # Clear existing tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get list of databases from manager
        databases = self.db_manager.get_databases()
        if databases:
            for db_name in databases:
                db_node = self.tree.insert("", tk.END, text=db_name, tags=("database",))
                # If this database is currently open, load its tables
                if self.db_manager.current_db == db_name:
                    self.refresh_tables(db_node)
                else:
                    # Show placeholder for unloaded database
                    self.tree.insert(db_node, tk.END, text="[Not Loaded]")
        else:
            # Show message when no databases exist
            self.tree.insert("", tk.END, text="No databases found. Create one using the context menu.")

    def refresh_tables(self, db_node):
        # Clear existing children under this database node
        try:
            children = self.tree.get_children(db_node)
            for child in children:
                try:
                    self.tree.delete(child)
                except tk.TclError:
                    # Handle case where item no longer exists
                    continue
        except tk.TclError:
            # Handle case where database node no longer exists
            return
        
        # Get tables for the current database
        tables = self.db_manager.get_tables()
        for table_name in tables:
            try:
                self.tree.insert(db_node, tk.END, text=table_name, tags=("table",))
            except tk.TclError:
                # Handle case where database node no longer exists
                break

    def on_right_click(self, event):
        # Identify the item clicked on
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            item_text = self.tree.item(item)["text"]
            tags = self.tree.item(item)["tags"]
            # Create context menu based on item type
            menu = tk.Menu(self, tearoff=0)
            if "database" in tags:
                menu.add_command(label="Open Database", command=lambda: self.open_database(item_text))
                menu.add_command(label="Delete Database", command=lambda: self.delete_database(item_text))
            elif "table" in tags:
                menu.add_command(label="View Schema", command=lambda: self.view_table_schema(item_text))
                menu.add_command(label="Delete Table", command=lambda: self.delete_table(item_text))
            elif "database" in tags and self.db_manager.current_db == item_text:
                menu.add_command(label="Create Table", command=self.create_new_table)
            else:
                menu.add_command(label="Create New Database", command=self.create_new_database)
            menu.post(event.x_root, event.y_root)
        else:
            # Right-click on empty space
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Create New Database", command=self.create_new_database)
            menu.post(event.x_root, event.y_root)

    def on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            try:
                item_text = self.tree.item(item)["text"]
                tags = self.tree.item(item)["tags"]
                if "database" in tags:
                    self.open_database(item_text)
                    self.refresh_tables(item)
            except tk.TclError:
                # Handle case where item no longer exists
                pass

    def create_new_database(self):
        # Prompt user for database name
        from tkinter import simpledialog, messagebox
        db_name = simpledialog.askstring("Create Database", "Enter database name:", parent=self)
        if db_name:
            if self.db_manager.create_database(db_name):
                messagebox.showinfo("Success", f"Database '{db_name}' created successfully.", parent=self)
                self.refresh_databases()
            else:
                messagebox.showerror("Error", f"Failed to create database '{db_name}'.", parent=self)

    def open_database(self, db_name):
        if self.db_manager.open_database(db_name):
            print(f"Opened database: {db_name}")
            self.refresh_databases()
        else:
            print(f"Failed to open database: {db_name}")

    def delete_database(self, db_name):
        # Placeholder for deleting a database
        print(f"Deleting database: {db_name}")
        # In a real implementation, confirm deletion and remove file

    def view_table_schema(self, table_name):
        # Placeholder for viewing table schema
        print(f"Viewing schema for table: {table_name}")
        schema = self.db_manager.get_table_schema(table_name)
        print(schema)

    def create_new_table(self):
        # Prompt user for table creation SQL
        from tkinter import simpledialog, messagebox
        table_sql = simpledialog.askstring("Create Table", "Enter CREATE TABLE SQL:", parent=self)
        if table_sql:
            try:
                self.db_manager.execute_query(table_sql)
                messagebox.showinfo("Success", "Table created successfully.", parent=self)
                self.refresh_databases()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create table: {e}", parent=self)

    def delete_table(self, table_name):
        # Confirm deletion and execute DROP TABLE
        from tkinter import messagebox
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete table '{table_name}'?", parent=self):
            try:
                self.db_manager.execute_query(f"DROP TABLE {table_name}")
                messagebox.showinfo("Success", f"Table '{table_name}' deleted successfully.", parent=self)
                self.refresh_databases()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete table: {e}", parent=self)

    def on_filter_change(self, event):
        """Handle filter text change."""
        filter_text = self.filter_entry.get().lower()
        self.filter_tree(filter_text)

    def filter_tree(self, filter_text):
        """Filter tree items based on text."""
        if not filter_text:
            # Show all items
            for item in self.tree.get_children():
                self.tree.item(item, open=False)
        else:
            # Hide items that don't match filter
            for item in self.tree.get_children():
                item_text = self.tree.item(item)["text"].lower()
                if filter_text in item_text:
                    self.tree.item(item, open=True)
                else:
                    self.tree.item(item, open=False)
