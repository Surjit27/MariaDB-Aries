import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

class SettingsManager:
    """Manages application settings including API keys and theme preferences."""
    
    def __init__(self, settings_file: str = "settings.json"):
        self.settings_file = settings_file
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from JSON file."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading settings: {e}")
                return self.get_default_settings()
        return self.get_default_settings()
    
    def save_settings(self) -> bool:
        """Save settings to JSON file."""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get_default_settings(self) -> Dict[str, Any]:
        """Get default settings."""
        return {
            "theme": "darkly",
            "api_keys": [],
            "selected_api_key": None,
            "window_geometry": "1200x800",
            "auto_save": True,
            "syntax_highlighting": True,
            "ai_autocomplete": True
        }
    
    def get_theme(self) -> str:
        """Get current theme."""
        return self.settings.get("theme", "darkly")
    
    def set_theme(self, theme: str) -> bool:
        """Set theme and save settings."""
        self.settings["theme"] = theme
        return self.save_settings()
    
    def add_api_key(self, name: str, api_key: str, provider: str = "gemini") -> bool:
        """Add a new API key."""
        if not name or not api_key:
            return False
        
        # Check if name already exists
        for key in self.settings["api_keys"]:
            if key["name"] == name:
                return False
        
        new_key = {
            "id": len(self.settings["api_keys"]) + 1,
            "name": name,
            "api_key": api_key,
            "provider": provider,
            "created_at": datetime.now().isoformat(),
            "last_used": None
        }
        
        self.settings["api_keys"].append(new_key)
        
        # If this is the first key, set it as selected
        if len(self.settings["api_keys"]) == 1:
            self.settings["selected_api_key"] = new_key["id"]
        
        return self.save_settings()
    
    def update_api_key(self, key_id: int, name: str = None, api_key: str = None) -> bool:
        """Update an existing API key."""
        for key in self.settings["api_keys"]:
            if key["id"] == key_id:
                if name is not None:
                    key["name"] = name
                if api_key is not None:
                    key["api_key"] = api_key
                key["updated_at"] = datetime.now().isoformat()
                return self.save_settings()
        return False
    
    def delete_api_key(self, key_id: int) -> bool:
        """Delete an API key."""
        self.settings["api_keys"] = [key for key in self.settings["api_keys"] if key["id"] != key_id]
        
        # If deleted key was selected, select another one or clear selection
        if self.settings["selected_api_key"] == key_id:
            if self.settings["api_keys"]:
                self.settings["selected_api_key"] = self.settings["api_keys"][0]["id"]
            else:
                self.settings["selected_api_key"] = None
        
        return self.save_settings()
    
    def get_api_keys(self) -> List[Dict[str, Any]]:
        """Get all API keys."""
        return self.settings["api_keys"]
    
    def get_selected_api_key(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected API key."""
        selected_id = self.settings.get("selected_api_key")
        if selected_id:
            for key in self.settings["api_keys"]:
                if key["id"] == selected_id:
                    return key
        return None
    
    def set_selected_api_key(self, key_id: int) -> bool:
        """Set the selected API key."""
        # Verify key exists
        for key in self.settings["api_keys"]:
            if key["id"] == key_id:
                self.settings["selected_api_key"] = key_id
                key["last_used"] = datetime.now().isoformat()
                return self.save_settings()
        return False
    
    def get_api_key_value(self) -> Optional[str]:
        """Get the value of the currently selected API key."""
        selected_key = self.get_selected_api_key()
        return selected_key["api_key"] if selected_key else None
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value."""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set a specific setting value."""
        self.settings[key] = value
        return self.save_settings()
