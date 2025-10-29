#!/usr/bin/env python3
"""
Test script for the Compact AI Modal functionality.
This script tests the compact AI modal without running the full application.
"""

import tkinter as tk
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ui.components.compact_ai_modal import CompactAIModal, CompactAITooltip
from ai.gemini_integration import GeminiIntegration
from db.enhanced_database_manager import EnhancedDatabaseManager

class MockSQLEditor:
    """Mock SQL editor for testing."""
    def __init__(self):
        self.editor = tk.Text()
        
class TestApp:
    """Test application for compact AI modal."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Compact AI Modal Test")
        self.root.geometry("800x600")
        
        # Initialize components
        self.db_manager = EnhancedDatabaseManager("test_databases")
        self.ai_integration = GeminiIntegration()
        self.sql_editor = MockSQLEditor()
        
        # Initialize compact AI modal
        self.compact_ai_modal = CompactAIModal(self.root, self.ai_integration, self.sql_editor, self.db_manager)
        self.compact_ai_tooltip = CompactAITooltip(self.root, self.ai_integration, self.sql_editor, self.db_manager)
        
        self.create_ui()
        
    def create_ui(self):
        """Create the test UI."""
        # Main frame
        main_frame = tk.Frame(self.root, bg="#2d2d2d")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame, text="Compact AI Modal Test", 
                              font=("Arial", 16, "bold"), 
                              fg="#ffffff", bg="#2d2d2d")
        title_label.pack(pady=20)
        
        # Description
        desc_label = tk.Label(main_frame, 
                             text="Test the compact AI modal and tooltip functionality", 
                             font=("Arial", 10), 
                             fg="#cccccc", bg="#2d2d2d")
        desc_label.pack(pady=10)
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg="#2d2d2d")
        button_frame.pack(pady=20)
        
        # Test buttons
        modal_btn = tk.Button(button_frame, text="🤖 Show Compact AI Modal", 
                             command=self.test_compact_modal,
                             bg="#007acc", fg="#ffffff", bd=0,
                             font=("Arial", 10), padx=20, pady=10,
                             activebackground="#005a9e", activeforeground="#ffffff")
        modal_btn.pack(side=tk.LEFT, padx=10)
        
        tooltip_btn = tk.Button(button_frame, text="💡 Show AI Tooltip", 
                               command=self.test_compact_tooltip,
                               bg="#28a745", fg="#ffffff", bd=0,
                               font=("Arial", 10), padx=20, pady=10,
                               activebackground="#1e7e34", activeforeground="#ffffff")
        tooltip_btn.pack(side=tk.LEFT, padx=10)
        
        # Instructions
        instructions = tk.Text(main_frame, height=8, width=60, 
                              font=("Consolas", 9),
                              bg="#404040", fg="#ffffff",
                              insertbackground="#ffffff", relief="flat", bd=1)
        instructions.pack(pady=20, fill=tk.BOTH, expand=True)
        
        instructions_text = """Test Instructions:

1. Click "Show Compact AI Modal" to test the compact modal
   - The modal should appear as a small floating window
   - It should auto-hide after 5 seconds of inactivity
   - You can type in it and press Enter to generate SQL
   - Press Escape to close it manually

2. Click "Show AI Tooltip" to test the compact tooltip
   - The tooltip should appear as an even smaller floating widget
   - It should be more compact than the modal
   - It should also auto-hide after a short time

3. Keyboard shortcuts:
   - Ctrl+Shift+A: Toggle compact AI modal
   - Ctrl+Shift+T: Show AI tooltip

4. Features to test:
   - Smart positioning (avoiding screen edges)
   - Auto-hide functionality
   - Focus management
   - SQL generation (if AI is available)
   - Error handling

Note: This is a test environment. The AI integration may not work without proper API keys.
"""
        
        instructions.insert("1.0", instructions_text)
        instructions.configure(state="disabled")
        
        # Bind keyboard shortcuts
        self.root.bind("<Control-Shift-A>", lambda event: self.test_compact_modal())
        self.root.bind("<Control-Shift-T>", lambda event: self.test_compact_tooltip())
        
    def test_compact_modal(self):
        """Test the compact AI modal."""
        print("Testing compact AI modal...")
        self.compact_ai_modal.show_modal()
        
    def test_compact_tooltip(self):
        """Test the compact AI tooltip."""
        print("Testing compact AI tooltip...")
        self.compact_ai_tooltip.show_tooltip()
        
    def run(self):
        """Run the test application."""
        print("Starting Compact AI Modal Test...")
        print("Press Ctrl+Shift+A for modal, Ctrl+Shift+T for tooltip")
        self.root.mainloop()

if __name__ == "__main__":
    app = TestApp()
    app.run()
