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
        """Save settings to JSON file with error handling."""
        try:
            print(f"DEBUG: save_settings called. api_keys count: {len(self.settings.get('api_keys', []))}")
            
            # Create directory if it doesn't exist
            dir_path = os.path.dirname(self.settings_file) if os.path.dirname(self.settings_file) else '.'
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            # Write directly to settings file (simpler approach)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
            
            # Verify the file was written correctly
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    saved_count = len(saved_data.get('api_keys', []))
                    print(f"DEBUG: Settings file verified. api_keys count in file: {saved_count}")
                    if saved_count != len(self.settings.get('api_keys', [])):
                        print(f"DEBUG: WARNING - Mismatch! In-memory: {len(self.settings.get('api_keys', []))}, File: {saved_count}")
            
            return True
        except IOError as e:
            print(f"ERROR: Error saving settings: {e}")
            import traceback
            traceback.print_exc()
            return False
        except Exception as e:
            print(f"ERROR: Unexpected error saving settings: {e}")
            import traceback
            traceback.print_exc()
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
        print(f"DEBUG: add_api_key() called with name='{name}', provider='{provider}'")
        print(f"DEBUG: Current api_keys before add: {len(self.settings.get('api_keys', []))}")
        
        if not name or not api_key:
            print(f"DEBUG: add_api_key failed - missing name or api_key")
            return False
        
        # Ensure api_keys list exists
        if "api_keys" not in self.settings:
            self.settings["api_keys"] = []
            print("DEBUG: Created api_keys list")
        
        # Check if name already exists
        for key in self.settings["api_keys"]:
            if key.get("name") == name:
                print(f"DEBUG: add_api_key failed - name '{name}' already exists")
                return False
        
        # Generate unique ID - use max ID + 1, or 1 if no keys exist
        max_id = max([key.get("id", 0) for key in self.settings["api_keys"]], default=0)
        new_id = max_id + 1
        
        new_key = {
            "id": new_id,
            "name": name,
            "api_key": api_key,
            "provider": provider,
            "created_at": datetime.now().isoformat(),
            "last_used": None
        }
        
        self.settings["api_keys"].append(new_key)
        print(f"DEBUG: Added API key with ID {new_id}, name '{name}'. Total keys in memory: {len(self.settings['api_keys'])}")
        print(f"DEBUG: New key structure: {new_key}")
        
        # If this is the first key, set it as selected
        if len(self.settings["api_keys"]) == 1:
            self.settings["selected_api_key"] = new_key["id"]
            print(f"DEBUG: Set as selected key (ID: {new_key['id']})")
        
        # Save to file
        saved = self.save_settings()
        print(f"DEBUG: Save settings returned: {saved}")
        
        # Verify immediately after save
        if saved:
            # Check in-memory
            in_mem_count = len(self.settings.get('api_keys', []))
            print(f"DEBUG: After save - in-memory count: {in_mem_count}")
            
            # Reload and check file
            reloaded = self.load_settings()
            file_count = len(reloaded.get('api_keys', []))
            print(f"DEBUG: After save - file count: {file_count}")
            
            if file_count != in_mem_count:
                print(f"DEBUG: ERROR - File count mismatch! Retrying save...")
                saved = self.save_settings()
        
        return saved
    
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
