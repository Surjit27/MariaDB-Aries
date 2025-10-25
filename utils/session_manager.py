import os
import json
import tkinter as tk
from typing import Dict, Any

class SessionManager:
    def __init__(self, session_path: str):
        """Initialize the session manager with a path to store session files."""
        self.session_path = session_path
        os.makedirs(os.path.dirname(session_path), exist_ok=True)

    def save_session(self, session_data: Dict[str, Any], session_name: str) -> bool:
        """Save the current session data to a JSON file."""
        session_file = os.path.join(self.session_path, f"{session_name}.json")
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
            print(f"Session saved to {session_file}")
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False

    def load_session(self, session_name: str) -> Dict[str, Any]:
        """Load session data from a JSON file."""
        session_file = os.path.join(self.session_path, f"{session_name}.json")
        if not os.path.exists(session_file):
            print(f"Session file {session_file} does not exist.")
            return {}
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading session: {e}")
            return {}

    def get_session_names(self) -> list:
        """Return a list of available session names."""
        if not os.path.exists(self.session_path):
            return []
        return [f.split('.json')[0] for f in os.listdir(self.session_path) if f.endswith('.json')]

    def prompt_save_session(self, parent: tk.Tk, current_data: Dict[str, Any]) -> bool:
        """Prompt user for session name and save the current session."""
        from tkinter import simpledialog, messagebox
        session_name = simpledialog.askstring("Save Session", "Enter session name:", parent=parent)
        if session_name:
            if self.save_session(current_data, session_name):
                messagebox.showinfo("Success", f"Session '{session_name}' saved successfully.", parent=parent)
                return True
            else:
                messagebox.showerror("Error", f"Failed to save session '{session_name}'.", parent=parent)
                return False
        return False

    def prompt_load_session(self, parent: tk.Tk) -> Dict[str, Any]:
        """Prompt user to select a session to load."""
        from tkinter import simpledialog, messagebox
        sessions = self.get_session_names()
        if not sessions:
            messagebox.showinfo("Info", "No saved sessions found.", parent=parent)
            return {}
        session_name = simpledialog.askstring("Load Session", "Enter session name to load:", parent=parent)
        if session_name and session_name in sessions:
            session_data = self.load_session(session_name)
            if session_data:
                messagebox.showinfo("Success", f"Session '{session_name}' loaded successfully.", parent=parent)
            else:
                messagebox.showerror("Error", f"Failed to load session '{session_name}'.", parent=parent)
            return session_data
        elif session_name:
            messagebox.showerror("Error", f"Session '{session_name}' not found.", parent=parent)
        return {}
