import tkinter as tk
import ttkbootstrap as ttk
import csv
import os
from io import StringIO
from tkinter import messagebox, filedialog

class ResultsViewerPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.current_columns = []
        self.current_data = []
        self.sort_column = None
        self.sort_reverse = False
        self.create_widgets()

    def create_widgets(self):
        label = ttk.Label(self, text="Query Results")
        label.pack(pady=5)
        
        # Treeview for displaying query results with increased size
        self.tree = ttk.Treeview(self, height=20)  # Increased height
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbar for treeview
        scrollbar_y = ttk.Scrollbar(self.tree, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar_y.set)
        
        scrollbar_x = ttk.Scrollbar(self.tree, orient=tk.HORIZONTAL, command=self.tree.xview)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.configure(xscrollcommand=scrollbar_x.set)
        
        # Bind column header click for sorting
        self.tree.bind("<Button-1>", self.on_header_click)
        # Bind right-click for context menu
        self.tree.bind("<Button-3>", self.on_right_click)
        
        # Buttons for data management
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Copy Selection", command=self.copy_selection).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Copy All", command=self.copy_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Export to CSV", command=self.export_to_csv).pack(side=tk.LEFT, padx=5)
        
        # Show initial empty state
        self.display_empty_state()

    def display_empty_state(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Show message when no query has been executed
        self.tree['columns'] = ('message',)
        self.tree.heading('#0', text='')
        self.tree.heading('message', text='No query executed yet')
        self.tree.column('message', width=400, anchor=tk.W)
        
        # Insert message
        self.tree.insert('', tk.END, text='', values=('Execute a SQL query to see results here',))
        self.current_columns = ['Message']
        self.current_data = [['', 'Execute a SQL query to see results here']]

    def display_results(self, columns, data):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Validate inputs
        if not columns or not isinstance(columns, list):
            columns = ['Result']
        if not data or not isinstance(data, list):
            data = []
        
        # Set columns with increased widths
        self.tree['columns'] = columns
        self.tree.heading('#0', text='Row')
        for col in columns:
            self.tree.heading(col, text=str(col))
            self.tree.column(col, width=200, anchor=tk.W)  # Increased from 120 to 200
        self.tree.column('#0', width=80, anchor=tk.W)  # Increased from 50 to 80
        
        # Insert data
        for i, row in enumerate(data, 1):
            # Convert row to list if it's a tuple
            if isinstance(row, tuple):
                row_values = list(row)
            elif isinstance(row, list):
                row_values = row
            else:
                row_values = [str(row)]
            
            # Ensure we have the right number of values
            while len(row_values) < len(columns):
                row_values.append('')
            
            # Truncate if too many values
            if len(row_values) > len(columns):
                row_values = row_values[:len(columns)]
            
            self.tree.insert('', tk.END, text=str(i), values=row_values)
        
        # Store for sorting and export
        self.current_columns = ['Row'] + columns
        self.current_data = []
        for i, row in enumerate(data, 1):
            if isinstance(row, tuple):
                row_values = [str(i)] + list(row)
            elif isinstance(row, list):
                row_values = [str(i)] + row
            else:
                row_values = [str(i), str(row)]
            self.current_data.append(row_values)
        
        self.sort_column = None
        self.sort_reverse = False

    def display_error(self, error_message):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Set single column for error message
        self.tree['columns'] = ('error',)
        self.tree.heading('#0', text='')
        self.tree.heading('error', text='Error')
        self.tree.column('error', width=400, anchor=tk.W)
        
        # Insert error message
        self.tree.insert('', tk.END, text='', values=(error_message,))
        self.current_columns = ['Error']
        self.current_data = [['', error_message]]

    def on_header_click(self, event):
        # Identify the column clicked
        region = self.tree.identify("region", event.x, event.y)
        if region == "heading":
            column_id = self.tree.identify_column(event.x)
            if column_id == '#0':
                column_index = 0
            else:
                column_index = int(column_id.replace('#', ''))
            self.sort_by_column(column_index)

    def sort_by_column(self, column_index):
        if not self.current_data or len(self.current_data[0]) <= column_index:
            return
        
        # Determine sort order
        if self.sort_column == column_index:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
        self.sort_column = column_index
        
        # Sort data
        def get_key(row):
            try:
                # Attempt to convert to float for numerical sorting
                return float(row[column_index])
            except ValueError:
                return row[column_index].lower()
        
        self.current_data.sort(key=get_key, reverse=self.sort_reverse)
        
        # Clear and reinsert sorted data
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self.current_data:
            self.tree.insert('', tk.END, text=row[0], values=row[1:])

    def copy_selection(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", "No rows selected to copy.")
            return
        
        output = StringIO()
        writer = csv.writer(output, delimiter='\t')
        writer.writerow(self.current_columns)
        for item in selected_items:
            row_data = [self.tree.item(item)['text']] + list(self.tree.item(item)['values'])
            writer.writerow(row_data)
        
        self.clipboard_clear()
        self.clipboard_append(output.getvalue())
        messagebox.showinfo("Info", "Selected data copied to clipboard.")

    def copy_all(self):
        if not self.current_data:
            messagebox.showinfo("Info", "No data to copy.")
            return
        
        output = StringIO()
        writer = csv.writer(output, delimiter='\t')
        writer.writerow(self.current_columns)
        for row in self.current_data:
            writer.writerow(row)
        
        self.clipboard_clear()
        self.clipboard_append(output.getvalue())
        messagebox.showinfo("Info", "All data copied to clipboard.")

    def export_to_csv(self):
        if not self.current_data:
            messagebox.showinfo("Info", "No data to export.")
            return
        
        file_path = tk.filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save CSV File"
        )
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(self.current_columns)
                    writer.writerows(self.current_data)
                messagebox.showinfo("Success", f"Data exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {e}")

    def on_right_click(self, event):
        """Handle right-click to show context menu."""
        # Identify the item clicked on
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            # Create context menu
            context_menu = tk.Menu(self, tearoff=0)
            context_menu.add_command(label="Copy Cell", command=self.copy_cell)
            context_menu.add_command(label="Copy Row", command=self.copy_row)
            context_menu.add_command(label="Copy All", command=self.copy_all)
            context_menu.add_separator()
            context_menu.add_command(label="Copy Error Message", command=self.copy_error_message)
            context_menu.post(event.x_root, event.y_root)

    def copy_cell(self):
        """Copy the content of the selected cell."""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        # Get the column that was clicked
        region = self.tree.identify("region", self.tree.winfo_pointerx() - self.tree.winfo_rootx(), 
                                   self.tree.winfo_pointery() - self.tree.winfo_rooty())
        if region == "cell":
            column = self.tree.identify_column(self.tree.winfo_pointerx() - self.tree.winfo_rootx())
            if column == '#0':
                cell_value = self.tree.item(item)['text']
            else:
                values = self.tree.item(item)['values']
                col_index = int(column.replace('#', '')) - 1
                if 0 <= col_index < len(values):
                    cell_value = values[col_index]
                else:
                    cell_value = ""
            
            self.clipboard_clear()
            self.clipboard_append(str(cell_value))
            messagebox.showinfo("Info", "Cell content copied to clipboard.")

    def copy_row(self):
        """Copy the entire selected row."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", "No row selected to copy.")
            return
        
        item = selected_items[0]
        row_data = [self.tree.item(item)['text']] + list(self.tree.item(item)['values'])
        
        # Format as tab-separated values
        output = StringIO()
        writer = csv.writer(output, delimiter='\t')
        writer.writerow(row_data)
        
        self.clipboard_clear()
        self.clipboard_append(output.getvalue())
        messagebox.showinfo("Info", "Row copied to clipboard.")

    def copy_error_message(self):
        """Copy error message from the results viewer."""
        if not self.current_data:
            messagebox.showinfo("Info", "No data to copy.")
            return
        
        # If this is an error display, copy the error message
        if len(self.current_data) > 0 and len(self.current_data[0]) > 1:
            error_msg = self.current_data[0][1]  # Error message is in the second column
            self.clipboard_clear()
            self.clipboard_append(error_msg)
            messagebox.showinfo("Info", "Error message copied to clipboard.")
        else:
            messagebox.showinfo("Info", "No error message to copy.")
