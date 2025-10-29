#!/usr/bin/env python3
"""
Test script for the Horizontal AI Modal component
"""

import tkinter as tk
import ttkbootstrap as ttk
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ui.components.horizontal_ai_modal import HorizontalAIModal
from db.enhanced_database_manager import EnhancedDatabaseManager
from ai.gemini_integration import GeminiIntegration

class TestApp:
    def __init__(self):
        self.root = ttk.Window(themename="darkly")
        self.root.title("Horizontal AI Modal Test")
        self.root.geometry("800x600")
        
        # Initialize components
        db_storage_path = os.path.join(os.getcwd(), "databases")
        self.db_manager = EnhancedDatabaseManager(db_storage_path)
        self.ai_integration = GeminiIntegration()
        
        # Create test UI
        self.create_ui()
        
    def create_ui(self):
        """Create the test UI."""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Horizontal AI Modal Test", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Instructions
        instructions = ttk.Label(main_frame, 
                                text="Click the button below to test the horizontal AI modal.\n"
                                     "The modal supports @ for table selection and # for column selection.",
                                font=("Arial", 10))
        instructions.pack(pady=(0, 20))
        
        # Test button
        test_btn = ttk.Button(main_frame, text="Show Horizontal AI Modal", 
                             command=self.show_modal)
        test_btn.pack(pady=10)
        
        # SQL Editor simulation
        editor_frame = ttk.LabelFrame(main_frame, text="SQL Editor (Simulation)")
        editor_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        self.editor = tk.Text(editor_frame, 
                             font=("Consolas", 12),
                             bg="#1e1e1e", fg="#ffffff",
                             insertbackground="#ffffff",
                             selectbackground="#404040",
                             selectforeground="#ffffff",
                             relief="flat", bd=1,
                             wrap=tk.NONE)
        
        editor_scrollbar = ttk.Scrollbar(editor_frame, orient=tk.VERTICAL, command=self.editor.yview)
        self.editor.configure(yscrollcommand=editor_scrollbar.set)
        
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        editor_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add some sample content
        self.editor.insert("1.0", "-- Sample SQL query\nSELECT * FROM users WHERE active = 1;")
        
        # Initialize horizontal AI modal
        self.horizontal_ai_modal = HorizontalAIModal(
            self.root,
            self.ai_integration,
            self,
            self.db_manager
        )
        
    def show_modal(self):
        """Show the horizontal AI modal."""
        # Get cursor position
        cursor_pos = self.editor.index(tk.INSERT)
        x, y = self.editor.bbox(cursor_pos)
        if x is not None and y is not None:
            # Convert to root coordinates
            root_x = self.editor.winfo_rootx() + x
            root_y = self.editor.winfo_rooty() + y + 20
            self.horizontal_ai_modal.show_at_position(root_x, root_y)
        else:
            # Fallback to center
            center_x = self.editor.winfo_rootx() + self.editor.winfo_width() // 2
            center_y = self.editor.winfo_rooty() + self.editor.winfo_height() // 2
            self.horizontal_ai_modal.show_at_position(center_x, center_y)
    
    def run(self):
        """Run the test application."""
        self.root.mainloop()

if __name__ == "__main__":
    app = TestApp()
    app.run()
