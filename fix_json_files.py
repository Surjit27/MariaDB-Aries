"""
Fix corrupted JSON files for query history and schemas
"""

import os
import json
import shutil
from datetime import datetime

def fix_json_file(file_path, default_data):
    """Fix corrupted JSON file by backing up and resetting."""
    try:
        # Create backup directory
        backup_dir = os.path.join(os.path.dirname(file_path), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup existing file if it exists
        if os.path.exists(file_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"{os.path.basename(file_path)}.{timestamp}.backup")
            shutil.copy2(file_path, backup_path)
            print(f"✅ Backed up {file_path} to {backup_path}")
        
        # Write default data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Fixed {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Fix all corrupted JSON files."""
    # Get project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(project_root, 'databases')
    
    print("🔧 Fixing corrupted JSON files...")
    print(f"Database path: {db_path}\n")
    
    # Fix query_history.json
    query_history_path = os.path.join(db_path, 'query_history.json')
    default_history = []
    fix_json_file(query_history_path, default_history)
    
    # Fix favorites.json
    favorites_path = os.path.join(db_path, 'favorites.json')
    default_favorites = []
    fix_json_file(favorites_path, default_favorites)
    
    # Fix schemas.json
    schemas_dir = os.path.join(db_path, 'schemas')
    os.makedirs(schemas_dir, exist_ok=True)
    schemas_path = os.path.join(schemas_dir, 'schemas.json')
    default_schemas = {}
    fix_json_file(schemas_path, default_schemas)
    
    print("\n✅ All JSON files fixed!")
    print("\nYou can now run the application:")
    print("python main.py")

if __name__ == "__main__":
    main()
