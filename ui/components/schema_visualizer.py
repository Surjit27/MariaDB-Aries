import tkinter as tk
import ttkbootstrap as ttk
from typing import List, Dict, Any, Callable
import json

class SchemaVisualizer(ttk.Frame):
    def __init__(self, parent, db_manager):
        super().__init__(parent)
        self.db_manager = db_manager
        self.create_widgets()
        self.refresh_schema()

    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Title
        title_label = ttk.Label(main_frame, text="Database Schema", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))

        # Controls
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(controls_frame, text="Refresh Schema", command=self.refresh_schema).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Export Schema", command=self.export_schema).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Generate ER Diagram", command=self.generate_er_diagram).pack(side=tk.LEFT, padx=5)

        # Schema tree
        schema_frame = ttk.Frame(main_frame)
        schema_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Treeview for schema
        self.schema_tree = ttk.Treeview(schema_frame, show="tree")
        self.schema_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        schema_scrollbar = ttk.Scrollbar(schema_frame, orient=tk.VERTICAL, command=self.schema_tree.yview)
        self.schema_tree.configure(yscrollcommand=schema_scrollbar.set)
        schema_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Schema details
        details_frame = ttk.LabelFrame(main_frame, text="Schema Details", padding=5)
        details_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.details_text = tk.Text(details_frame, height=10, wrap=tk.WORD)
        self.details_text.pack(fill=tk.BOTH, expand=True)

        # Bind events
        self.schema_tree.bind("<<TreeviewSelect>>", self.on_schema_select)

    def refresh_schema(self):
        """Refresh the schema display."""
        self.schema_tree.delete(*self.schema_tree.get_children())
        
        if not self.db_manager.current_db:
            self.schema_tree.insert("", tk.END, text="No database selected")
            return

        # Get tables
        tables = self.db_manager.get_tables()
        
        for table in tables:
            table_node = self.schema_tree.insert("", tk.END, text=table, tags=("table",))
            
            # Add columns
            schema = self.db_manager.get_table_schema(table)
            if schema and 'columns' in schema:
                columns_node = self.schema_tree.insert(table_node, tk.END, text="Columns", tags=("columns",))
                for col in schema['columns']:
                    col_info = f"{col['name']} ({col['type']})"
                    if col['pk']:
                        col_info += " [PK]"
                    if col['notnull']:
                        col_info += " [NOT NULL]"
                    self.schema_tree.insert(columns_node, tk.END, text=col_info, tags=("column",))
            
            # Add foreign keys
            if schema and 'foreign_keys' in schema and schema['foreign_keys']:
                fk_node = self.schema_tree.insert(table_node, tk.END, text="Foreign Keys", tags=("foreign_keys",))
                for fk in schema['foreign_keys']:
                    fk_info = f"{fk['from']} -> {fk['table']}.{fk['to']}"
                    self.schema_tree.insert(fk_node, tk.END, text=fk_info, tags=("foreign_key",))

    def on_schema_select(self, event):
        """Handle schema selection."""
        selection = self.schema_tree.selection()
        if not selection:
            return
        
        item = self.schema_tree.item(selection[0])
        tags = item['tags']
        
        self.details_text.delete(1.0, tk.END)
        
        if "table" in tags:
            self.show_table_details(item['text'])
        elif "column" in tags:
            self.show_column_details(item['text'])
        elif "foreign_key" in tags:
            self.show_foreign_key_details(item['text'])

    def show_table_details(self, table_name):
        """Show detailed information about a table."""
        schema = self.db_manager.get_table_schema(table_name)
        if not schema:
            return
        
        details = f"Table: {table_name}\n\n"
        details += "Columns:\n"
        
        for col in schema.get('columns', []):
            details += f"  • {col['name']} ({col['type']})"
            if col['pk']:
                details += " [PRIMARY KEY]"
            if col['notnull']:
                details += " [NOT NULL]"
            if col['default']:
                details += f" [DEFAULT: {col['default']}]"
            details += "\n"
        
        if schema.get('foreign_keys'):
            details += "\nForeign Keys:\n"
            for fk in schema['foreign_keys']:
                details += f"  • {fk['from']} -> {fk['table']}.{fk['to']}\n"
        
        self.details_text.insert(1.0, details)

    def show_column_details(self, column_info):
        """Show detailed information about a column."""
        self.details_text.insert(1.0, f"Column: {column_info}")

    def show_foreign_key_details(self, fk_info):
        """Show detailed information about a foreign key."""
        self.details_text.insert(1.0, f"Foreign Key: {fk_info}")

    def export_schema(self):
        """Export schema to file."""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            schema_data = {}
            tables = self.db_manager.get_tables()
            for table in tables:
                schema_data[table] = self.db_manager.get_table_schema(table)
            
            with open(filename, 'w') as f:
                json.dump(schema_data, f, indent=2)
            
            from tkinter import messagebox
            messagebox.showinfo("Success", f"Schema exported to {filename}")

    def generate_er_diagram(self):
        """Generate a simple ER diagram representation."""
        if not self.db_manager.current_db:
            from tkinter import messagebox
            messagebox.showwarning("Warning", "No database selected")
            return
        
        # Create a simple text-based ER diagram
        er_diagram = "Entity-Relationship Diagram\n"
        er_diagram += "=" * 50 + "\n\n"
        
        tables = self.db_manager.get_tables()
        for table in tables:
            schema = self.db_manager.get_table_schema(table)
            if not schema:
                continue
            
            er_diagram += f"Entity: {table}\n"
            er_diagram += "-" * (len(table) + 8) + "\n"
            
            # Primary keys
            pk_columns = [col for col in schema.get('columns', []) if col.get('pk')]
            if pk_columns:
                er_diagram += "Primary Keys:\n"
                for col in pk_columns:
                    er_diagram += f"  • {col['name']} ({col['type']})\n"
            
            # Foreign keys
            if schema.get('foreign_keys'):
                er_diagram += "Foreign Keys:\n"
                for fk in schema['foreign_keys']:
                    er_diagram += f"  • {fk['from']} -> {fk['table']}.{fk['to']}\n"
            
            er_diagram += "\n"
        
        # Show in a new window
        self.show_er_diagram_window(er_diagram)

    def show_er_diagram_window(self, diagram):
        """Show ER diagram in a new window."""
        window = tk.Toplevel(self)
        window.title("ER Diagram")
        window.geometry("600x400")
        
        text_widget = tk.Text(window, wrap=tk.WORD, font=("Courier", 10))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, diagram)
        text_widget.config(state=tk.DISABLED)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(window, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
