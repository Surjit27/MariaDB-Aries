import csv
import json
import sqlite3
import os
from typing import List, Dict, Any, Tuple
from datetime import datetime

class DataExportImport:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def export_to_csv(self, table_name: str, filename: str = None) -> bool:
        """Export table data to CSV file."""
        if not self.db_manager.connection:
            return False
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{table_name}_{timestamp}.csv"
        
        try:
            # Get table data
            columns, data = self.db_manager.get_table_data(table_name, limit=10000)
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(columns)  # Header
                writer.writerows(data)   # Data
            
            print(f"Data exported to {filename}")
            return True
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False

    def export_to_json(self, table_name: str, filename: str = None) -> bool:
        """Export table data to JSON file."""
        if not self.db_manager.connection:
            return False
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{table_name}_{timestamp}.json"
        
        try:
            # Get table data
            columns, data = self.db_manager.get_table_data(table_name, limit=10000)
            
            # Convert to list of dictionaries
            json_data = []
            for row in data:
                json_data.append(dict(zip(columns, row)))
            
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(json_data, jsonfile, indent=2, default=str)
            
            print(f"Data exported to {filename}")
            return True
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return False

    def export_to_sql(self, table_name: str, filename: str = None) -> bool:
        """Export table data to SQL INSERT statements."""
        if not self.db_manager.connection:
            return False
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{table_name}_{timestamp}.sql"
        
        try:
            # Get table data
            columns, data = self.db_manager.get_table_data(table_name, limit=10000)
            
            with open(filename, 'w', encoding='utf-8') as sqlfile:
                sqlfile.write(f"-- Export of table {table_name}\n")
                sqlfile.write(f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for row in data:
                    # Escape single quotes in values
                    escaped_values = []
                    for value in row:
                        if value is None:
                            escaped_values.append("NULL")
                        elif isinstance(value, str):
                            escaped_values.append(f"'{value.replace(chr(39), chr(39)+chr(39))}'")
                        else:
                            escaped_values.append(str(value))
                    
                    values_str = ", ".join(escaped_values)
                    sqlfile.write(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({values_str});\n")
            
            print(f"Data exported to {filename}")
            return True
        except Exception as e:
            print(f"Error exporting to SQL: {e}")
            return False

    def import_from_csv(self, table_name: str, filename: str) -> bool:
        """Import data from CSV file."""
        if not self.db_manager.connection:
            return False
        
        try:
            with open(filename, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                columns = next(reader)  # Header row
                
                # Prepare INSERT statement
                placeholders = ", ".join(["?" for _ in columns])
                insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                
                # Insert data
                for row in reader:
                    self.db_manager.cursor.execute(insert_sql, row)
                
                self.db_manager.connection.commit()
                print(f"Data imported from {filename}")
                return True
        except Exception as e:
            print(f"Error importing from CSV: {e}")
            return False

    def import_from_json(self, table_name: str, filename: str) -> bool:
        """Import data from JSON file."""
        if not self.db_manager.connection:
            return False
        
        try:
            with open(filename, 'r', encoding='utf-8') as jsonfile:
                data = json.load(jsonfile)
            
            if not data:
                print("No data to import")
                return False
            
            # Get columns from first record
            columns = list(data[0].keys())
            placeholders = ", ".join(["?" for _ in columns])
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            # Insert data
            for record in data:
                values = [record.get(col) for col in columns]
                self.db_manager.cursor.execute(insert_sql, values)
            
            self.db_manager.connection.commit()
            print(f"Data imported from {filename}")
            return True
        except Exception as e:
            print(f"Error importing from JSON: {e}")
            return False

    def backup_database(self, db_name: str, backup_path: str = None) -> bool:
        """Create a complete database backup."""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{db_name}_backup_{timestamp}.db"
        
        try:
            # Get database file path
            db_file = os.path.join(self.db_manager.db_path, f"{db_name}.db")
            if not os.path.exists(db_file):
                print(f"Database {db_name} not found")
                return False
            
            # Copy database file
            import shutil
            shutil.copy2(db_file, backup_path)
            print(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False

    def restore_database(self, backup_path: str, db_name: str) -> bool:
        """Restore database from backup."""
        try:
            if not os.path.exists(backup_path):
                print(f"Backup file {backup_path} not found")
                return False
            
            # Target database file
            target_file = os.path.join(self.db_manager.db_path, f"{db_name}.db")
            
            # Copy backup to target
            import shutil
            shutil.copy2(backup_path, target_file)
            print(f"Database restored from {backup_path}")
            return True
        except Exception as e:
            print(f"Error restoring database: {e}")
            return False

    def export_schema(self, filename: str = None) -> bool:
        """Export database schema to SQL file."""
        if not self.db_manager.connection:
            return False
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"schema_{timestamp}.sql"
        
        try:
            with open(filename, 'w', encoding='utf-8') as sqlfile:
                sqlfile.write(f"-- Database Schema Export\n")
                sqlfile.write(f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Get all tables
                tables = self.db_manager.get_tables()
                
                for table in tables:
                    # Get CREATE TABLE statement
                    self.db_manager.cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
                    result = self.db_manager.cursor.fetchone()
                    
                    if result and result[0]:
                        sqlfile.write(f"-- Table: {table}\n")
                        sqlfile.write(f"{result[0]};\n\n")
                
                # Get indexes
                self.db_manager.cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
                indexes = self.db_manager.cursor.fetchall()
                
                if indexes:
                    sqlfile.write("-- Indexes\n")
                    for index in indexes:
                        sqlfile.write(f"{index[0]};\n")
            
            print(f"Schema exported to {filename}")
            return True
        except Exception as e:
            print(f"Error exporting schema: {e}")
            return False

    def get_export_formats(self) -> List[str]:
        """Get list of supported export formats."""
        return ["CSV", "JSON", "SQL", "Schema"]

    def get_import_formats(self) -> List[str]:
        """Get list of supported import formats."""
        return ["CSV", "JSON"]
