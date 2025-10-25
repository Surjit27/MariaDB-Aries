import tkinter as tk
import ttkbootstrap as ttk
from typing import List, Dict, Any, Callable

class QueryBuilder(ttk.Frame):
    def __init__(self, parent, db_manager, on_query_generated: Callable = None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.on_query_generated = on_query_generated
        self.selected_tables = []
        self.selected_columns = []
        self.where_conditions = []
        self.join_conditions = []
        self.create_widgets()

    def create_widgets(self):
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
        title_label = ttk.Label(scrollable_frame, text="Query Builder", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))

        # Tables selection
        tables_frame = ttk.LabelFrame(scrollable_frame, text="Tables", padding=5)
        tables_frame.pack(fill=tk.X, pady=5)

        self.tables_listbox = tk.Listbox(tables_frame, selectmode=tk.MULTIPLE, height=4)
        self.tables_listbox.pack(fill=tk.X)
        self.tables_listbox.bind('<<ListboxSelect>>', self.on_table_selection_change)
        
        ttk.Button(tables_frame, text="Refresh Tables", command=self.refresh_tables).pack(pady=2)

        # Columns selection
        columns_frame = ttk.LabelFrame(scrollable_frame, text="Columns", padding=5)
        columns_frame.pack(fill=tk.X, pady=5)

        self.columns_listbox = tk.Listbox(columns_frame, selectmode=tk.MULTIPLE, height=4)
        self.columns_listbox.pack(fill=tk.X)

        # WHERE conditions
        where_frame = ttk.LabelFrame(scrollable_frame, text="WHERE Conditions", padding=5)
        where_frame.pack(fill=tk.X, pady=5)

        where_input_frame = ttk.Frame(where_frame)
        where_input_frame.pack(fill=tk.X)
        
        ttk.Label(where_input_frame, text="Column:").pack(side=tk.LEFT)
        self.where_column = ttk.Combobox(where_input_frame, width=15)
        self.where_column.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(where_input_frame, text="Operator:").pack(side=tk.LEFT, padx=(10, 0))
        self.where_operator = ttk.Combobox(where_input_frame, width=10, 
                                         values=["=", "!=", "<", ">", "<=", ">=", "LIKE", "IN", "BETWEEN"])
        self.where_operator.pack(side=tk.LEFT, padx=5)
        self.where_operator.set("=")
        
        ttk.Label(where_input_frame, text="Value:").pack(side=tk.LEFT, padx=(10, 0))
        self.where_value = ttk.Entry(where_input_frame, width=15)
        self.where_value.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(where_input_frame, text="Add", command=self.add_where_condition).pack(side=tk.LEFT, padx=5)

        # WHERE conditions list
        self.where_conditions_listbox = tk.Listbox(where_frame, height=3)
        self.where_conditions_listbox.pack(fill=tk.X, pady=2)
        
        ttk.Button(where_frame, text="Remove Selected", command=self.remove_where_condition).pack()

        # ORDER BY
        order_frame = ttk.LabelFrame(scrollable_frame, text="ORDER BY", padding=5)
        order_frame.pack(fill=tk.X, pady=5)

        order_input_frame = ttk.Frame(order_frame)
        order_input_frame.pack(fill=tk.X)
        
        ttk.Label(order_input_frame, text="Column:").pack(side=tk.LEFT)
        self.order_column = ttk.Combobox(order_input_frame, width=15)
        self.order_column.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(order_input_frame, text="Direction:").pack(side=tk.LEFT, padx=(10, 0))
        self.order_direction = ttk.Combobox(order_input_frame, width=10, values=["ASC", "DESC"])
        self.order_direction.pack(side=tk.LEFT, padx=5)
        self.order_direction.set("ASC")
        
        ttk.Button(order_input_frame, text="Add", command=self.add_order_by).pack(side=tk.LEFT, padx=5)

        # ORDER BY list
        self.order_by_listbox = tk.Listbox(order_frame, height=2)
        self.order_by_listbox.pack(fill=tk.X, pady=2)
        
        ttk.Button(order_frame, text="Remove Selected", command=self.remove_order_by).pack()

        # Generate Query button
        ttk.Button(scrollable_frame, text="Generate SQL Query", command=self.generate_query).pack(pady=10)

        # Generated query display
        query_frame = ttk.LabelFrame(scrollable_frame, text="Generated Query", padding=5)
        query_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.query_text = tk.Text(query_frame, height=6, wrap=tk.WORD)
        self.query_text.pack(fill=tk.BOTH, expand=True)

        # Buttons for generated query
        query_buttons_frame = ttk.Frame(query_frame)
        query_buttons_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(query_buttons_frame, text="Copy Query", command=self.copy_query).pack(side=tk.LEFT, padx=5)
        ttk.Button(query_buttons_frame, text="Execute Query", command=self.execute_query).pack(side=tk.LEFT, padx=5)
        ttk.Button(query_buttons_frame, text="Save as Favorite", command=self.save_as_favorite).pack(side=tk.LEFT, padx=5)

        # Initialize
        self.refresh_tables()

    def refresh_tables(self):
        """Refresh the tables list."""
        self.tables_listbox.delete(0, tk.END)
        tables = self.db_manager.get_tables()
        for table in tables:
            self.tables_listbox.insert(tk.END, table)

    def on_table_selection_change(self, event=None):
        """Handle table selection change."""
        selected_indices = self.tables_listbox.curselection()
        self.selected_tables = [self.tables_listbox.get(i) for i in selected_indices]
        
        # Update columns list
        self.columns_listbox.delete(0, tk.END)
        if self.selected_tables:
            # Get columns from first selected table
            table_name = self.selected_tables[0]
            schema = self.db_manager.get_table_schema(table_name)
            if schema and 'columns' in schema:
                for col in schema['columns']:
                    self.columns_listbox.insert(tk.END, f"{table_name}.{col['name']}")

    def add_where_condition(self):
        """Add a WHERE condition."""
        column = self.where_column.get()
        operator = self.where_operator.get()
        value = self.where_value.get()
        
        if column and operator and value:
            condition = f"{column} {operator} '{value}'"
            self.where_conditions.append(condition)
            self.where_conditions_listbox.insert(tk.END, condition)
            
            # Clear inputs
            self.where_column.set("")
            self.where_value.delete(0, tk.END)

    def remove_where_condition(self):
        """Remove selected WHERE condition."""
        selected_indices = self.where_conditions_listbox.curselection()
        for i in reversed(selected_indices):
            self.where_conditions_listbox.delete(i)
            del self.where_conditions[i]

    def add_order_by(self):
        """Add ORDER BY clause."""
        column = self.order_column.get()
        direction = self.order_direction.get()
        
        if column:
            order_clause = f"{column} {direction}"
            self.order_by_listbox.insert(tk.END, order_clause)

    def remove_order_by(self):
        """Remove selected ORDER BY clause."""
        selected_indices = self.order_by_listbox.curselection()
        for i in reversed(selected_indices):
            self.order_by_listbox.delete(i)

    def generate_query(self):
        """Generate SQL query from builder selections."""
        if not self.selected_tables:
            self.query_text.delete(1.0, tk.END)
            self.query_text.insert(1.0, "-- Please select at least one table")
            return

        # Build SELECT clause
        selected_indices = self.columns_listbox.curselection()
        if selected_indices:
            columns = [self.columns_listbox.get(i) for i in selected_indices]
            select_clause = f"SELECT {', '.join(columns)}"
        else:
            select_clause = "SELECT *"

        # Build FROM clause
        from_clause = f"FROM {', '.join(self.selected_tables)}"

        # Build WHERE clause
        where_clause = ""
        if self.where_conditions:
            where_clause = f"WHERE {' AND '.join(self.where_conditions)}"

        # Build ORDER BY clause
        order_by_clause = ""
        order_items = [self.order_by_listbox.get(i) for i in range(self.order_by_listbox.size())]
        if order_items:
            order_by_clause = f"ORDER BY {', '.join(order_items)}"

        # Combine query
        query_parts = [select_clause, from_clause, where_clause, order_by_clause]
        query = ' '.join([part for part in query_parts if part]) + ";"

        self.query_text.delete(1.0, tk.END)
        self.query_text.insert(1.0, query)

    def copy_query(self):
        """Copy generated query to clipboard."""
        query = self.query_text.get(1.0, tk.END).strip()
        self.clipboard_clear()
        self.clipboard_append(query)

    def execute_query(self):
        """Execute the generated query."""
        query = self.query_text.get(1.0, tk.END).strip()
        if query and self.on_query_generated:
            self.on_query_generated(query)

    def save_as_favorite(self):
        """Save query as favorite."""
        query = self.query_text.get(1.0, tk.END).strip()
        if query:
            from tkinter import simpledialog
            name = simpledialog.askstring("Save Favorite", "Enter name for this query:")
            if name:
                self.db_manager.add_to_favorites(query, name)

    def bind_events(self):
        """Bind events for interactive updates."""
        self.tables_listbox.bind('<<ListboxSelect>>', self.on_table_selection_change)
