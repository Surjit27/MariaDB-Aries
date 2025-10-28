import sqlite3
import os
import json
import pickle
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from sql_engine.simple_sql_compiler import SimpleSQLCompiler

class EnhancedDatabaseManager:
    def __init__(self, db_path: str):
        """Enhanced database manager with advanced features."""
        self.db_path = db_path
        self.current_db = None
        self.connection = None
        self.cursor = None
        self.sql_compiler = SimpleSQLCompiler()
        self.query_history = []
        self.favorites = []
        self.schemas = {}
        
        # Ensure directories exist
        os.makedirs(db_path, exist_ok=True)
        os.makedirs(os.path.join(db_path, "backups"), exist_ok=True)
        os.makedirs(os.path.join(db_path, "schemas"), exist_ok=True)
        
        # Load saved data
        self.load_query_history()
        self.load_favorites()
        self.load_schemas()

    def create_database(self, db_name: str) -> bool:
        """Create a new database with enhanced features."""
        db_file = os.path.join(self.db_path, f"{db_name}.db")
        try:
            conn = sqlite3.connect(db_file)
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            conn.close()
            print(f"Database created successfully: {db_file}")
            return self.open_database(db_name)
        except sqlite3.Error as e:
            print(f"Error creating database: {e}")
            return False

    def open_database(self, db_name: str) -> bool:
        """Open database with enhanced connection management."""
        db_file = os.path.join(self.db_path, f"{db_name}.db")
        if not os.path.exists(db_file):
            print(f"Database {db_name} does not exist.")
            return False
        try:
            self.connection = sqlite3.connect(db_file)
            self.cursor = self.connection.cursor()
            self.current_db = db_name
            # Enable foreign key constraints
            self.cursor.execute("PRAGMA foreign_keys = ON")
            # Load schema information
            self.load_database_schema()
            return True
        except sqlite3.Error as e:
            print(f"Error opening database: {e}")
            return False

    def execute_query(self, query: str, params: tuple = ()) -> Tuple[List[str], List[Any], Optional[str]]:
        """Execute query with enhanced error handling and history."""
        # Split multiple statements by semicolon, but be careful with semicolons in strings
        statements = self._split_sql_statements(query)
        
        if not statements:
            return [], [], "No valid SQL statements found"
        
        # If multiple statements, execute them one by one
        if len(statements) > 1:
            return self._execute_multiple_statements(statements)
        
        # Single statement
        query_upper = statements[0].strip().upper()
        
        # Handle special commands
        if query_upper.startswith("CREATE DATABASE"):
            db_name = self._extract_database_name(statements[0])
            if db_name:
                if self.create_database(db_name):
                    return [], [], None
                else:
                    return [], [], f"Failed to create database '{db_name}'"
            else:
                return [], [], "Invalid CREATE DATABASE syntax"
        
        if query_upper.startswith("USE"):
            db_name = self._extract_database_name(statements[0])
            if db_name:
                if self.open_database(db_name):
                    return [], [], None
                else:
                    return [], [], f"Failed to open database '{db_name}'"
            else:
                return [], [], "Invalid USE DATABASE syntax"
        
        if query_upper.startswith("DROP DATABASE"):
            db_name = self._extract_database_name(statements[0])
            if db_name:
                if self.drop_database(db_name):
                    return [], [], None
                else:
                    return [], [], f"Failed to drop database '{db_name}'"
            else:
                return [], [], "Invalid DROP DATABASE syntax"
        
        # For other queries, need an open database
        if not self.connection or not self.cursor:
            return [], [], "No database is currently open. Please create and open a database first."
        
        try:
            # Compile the SQL query
            compiled_query = self.sql_compiler.compile_sql(statements[0])
            print(f"Original query: {statements[0]}")
            print(f"Compiled query: {compiled_query}")
            
            # Execute query
            self.cursor.execute(compiled_query, params)
            
            # Add to query history
            self.add_to_history(statements[0], "success")
            
            if query_upper.startswith("SELECT"):
                column_names = [description[0] for description in self.cursor.description]
                results = self.cursor.fetchall()
                return column_names, results, None
            else:
                self.connection.commit()
                return [], [], None
                
        except sqlite3.Error as e:
            error_msg = f"Query execution error: {e}"
            print(error_msg)
            self.add_to_history(statements[0], f"error: {e}")
            return [], [], error_msg

    def _execute_multiple_statements(self, statements: List[str]) -> Tuple[List[str], List[Any], Optional[str]]:
        """Execute multiple SQL statements."""
        if not self.connection or not self.cursor:
            return [], [], "No database is currently open. Please create and open a database first."
        
        try:
            results = []
            column_names = []
            executed_count = 0
            
            for i, statement in enumerate(statements):
                statement = statement.strip()
                if not statement:
                    continue
                
                print(f"Executing statement {i+1}: {statement[:50]}...")
                
                try:
                    # Compile the SQL query
                    compiled_query = self.sql_compiler.compile_sql(statement)
                    print(f"Compiled: {compiled_query[:100]}...")
                    
                    # Execute query
                    self.cursor.execute(compiled_query)
                    executed_count += 1
                    
                    # If it's a SELECT statement, collect results
                    if statement.upper().startswith("SELECT"):
                        if not column_names:  # First SELECT statement
                            column_names = [description[0] for description in self.cursor.description]
                        results.extend(self.cursor.fetchall())
                        
                except sqlite3.Error as e:
                    print(f"Error in statement {i+1}: {e}")
                    # Continue with other statements
                    continue
            
            # Commit all changes
            self.connection.commit()
            
            # Add to history
            self.add_to_history("; ".join(statements), "success")
            
            if results:
                return column_names, results, None
            else:
                return [], [], f"Executed {executed_count} statements successfully"
                
        except Exception as e:
            error_msg = f"Error executing multiple statements: {e}"
            print(error_msg)
            self.add_to_history("; ".join(statements), f"error: {e}")
            return [], [], error_msg

    def add_to_history(self, query: str, status: str):
        """Add query to history."""
        try:
            # Clean the query
            query = query.strip()
            if not query:
                return
            
            # Create history entry
            history_entry = {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "status": status,
                "database": self.current_db or "None",
                "id": len(self.query_history) + 1  # Add unique ID
            }
            
            # Add to history
            self.query_history.append(history_entry)
            
            # Keep only last 100 queries
            if len(self.query_history) > 100:
                self.query_history = self.query_history[-100:]
            
            # Save to JSON file
            self.save_query_history()
            
            print(f"Query added to history: {query[:50]}... (Status: {status})")
            
        except Exception as e:
            print(f"Error adding query to history: {e}")

    def add_to_favorites(self, query: str, name: str):
        """Add query to favorites."""
        self.favorites.append({
            "name": name,
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "database": self.current_db
        })
        self.save_favorites()

    def get_query_history(self) -> List[Dict]:
        """Get query history."""
        return self.query_history

    def get_favorites(self) -> List[Dict]:
        """Get favorite queries."""
        return self.favorites
    
    def create_database(self, db_name: str) -> bool:
        """Create a new database file."""
        try:
            db_path = os.path.join(self.db_path, f"{db_name}.db")
            
            # Check if database already exists
            if os.path.exists(db_path):
                print(f"Database {db_name} already exists")
                return False
            
            # Create the database file by connecting to it
            temp_conn = sqlite3.connect(db_path)
            temp_conn.close()
            
            print(f"Database {db_name} created successfully at {db_path}")
            return True
            
        except Exception as e:
            print(f"Error creating database {db_name}: {e}")
            return False
    
    def switch_database(self, db_name: str) -> bool:
        """Switch to a different database."""
        try:
            db_path = os.path.join(self.db_path, f"{db_name}.db")
            
            if not os.path.exists(db_path):
                print(f"Database {db_name} does not exist")
                return False
            
            # Close current connection if exists
            if self.connection:
                self.connection.close()
            
            # Connect to new database
            self.connection = sqlite3.connect(db_path)
            self.cursor = self.connection.cursor()
            self.current_db = db_name
            
            print(f"Switched to database: {db_name}")
            return True
            
        except Exception as e:
            print(f"Error switching to database {db_name}: {e}")
            return False
    
    def get_database_schema_for_ai(self) -> Dict[str, Any]:
        if not self.connection or not self.cursor:
            return {
                "database_name": "No database",
                "tables": [],
                "relationships": []
            }
        
        try:
            # Get all tables
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in self.cursor.fetchall()]
            
            schema = {
                "database_name": self.current_db or "Unknown",
                "tables": [],
                "relationships": []
            }
            
            # Get schema for each table
            for table_name in tables:
                table_info = {
                    "table_name": table_name,
                    "columns": []
                }
                
                # Get column information
                self.cursor.execute(f"PRAGMA table_info({table_name})")
                columns = self.cursor.fetchall()
                
                for col in columns:
                    col_info = {
                        "name": col[1],
                        "type": col[2],
                        "nullable": not col[3],  # NOT NULL is 1, nullable is 0
                        "primary_key": bool(col[5])  # Primary key is 1
                    }
                    table_info["columns"].append(col_info)
                
                # Get foreign key relationships
                self.cursor.execute(f"PRAGMA foreign_key_list({table_name})")
                foreign_keys = self.cursor.fetchall()
                
                for fk in foreign_keys:
                    relationship = {
                        "from_table": table_name,
                        "from_column": fk[3],  # Column name
                        "to_table": fk[2],     # Referenced table
                        "to_column": fk[4]     # Referenced column
                    }
                    schema["relationships"].append(relationship)
                
                schema["tables"].append(table_info)
            
            return schema
            
        except Exception as e:
            print(f"Error getting database schema: {e}")
            return {
                "database_name": self.current_db or "Unknown",
                "tables": [],
                "relationships": []
            }
    
    def force_save_history(self):
        """Force save query history to JSON file."""
        try:
            self.save_query_history()
            print("Query history force saved successfully")
        except Exception as e:
            print(f"Error force saving query history: {e}")
    
    def get_history_count(self) -> int:
        """Get the number of queries in history."""
        return len(self.query_history)
    
    def clear_query_history(self):
        """Clear all query history."""
        self.query_history = []
        self.save_query_history()
        print("Query history cleared")
    
    def force_save_history(self):
        """Force save query history to JSON file."""
        try:
            self.save_query_history()
            print("Query history force saved successfully")
        except Exception as e:
            print(f"Error force saving query history: {e}")
    
    def get_history_count(self) -> int:
        """Get the number of queries in history."""
        return len(self.query_history)
    
    def clear_query_history(self):
        """Clear all query history."""
        self.query_history = []
        self.save_query_history()
        print("Query history cleared")

    def load_database_schema(self):
        """Load and cache database schema information."""
        if not self.connection:
            return
        
        try:
            # Get all tables
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in self.cursor.fetchall()]
            
            schema = {}
            for table in tables:
                # Get table info
                self.cursor.execute(f"PRAGMA table_info({table})")
                columns = []
                for row in self.cursor.fetchall():
                    columns.append({
                        "cid": row[0],
                        "name": row[1],
                        "type": row[2],
                        "notnull": bool(row[3]),
                        "default": row[4],
                        "pk": bool(row[5])
                    })
                
                # Get foreign keys
                self.cursor.execute(f"PRAGMA foreign_key_list({table})")
                foreign_keys = []
                for row in self.cursor.fetchall():
                    foreign_keys.append({
                        "id": row[0],
                        "seq": row[1],
                        "table": row[2],
                        "from": row[3],
                        "to": row[4],
                        "on_update": row[5],
                        "on_delete": row[6],
                        "match": row[7]
                    })
                
                schema[table] = {
                    "columns": columns,
                    "foreign_keys": foreign_keys
                }
            
            self.schemas[self.current_db] = schema
            self.save_schemas()
            
        except sqlite3.Error as e:
            print(f"Error loading schema: {e}")

    def get_table_schema(self, table_name: str) -> Dict:
        """Get detailed schema for a table."""
        if self.current_db in self.schemas and table_name in self.schemas[self.current_db]:
            return self.schemas[self.current_db][table_name]
        return {}

    def backup_database(self, db_name: str) -> bool:
        """Create a backup of the database."""
        try:
            source_file = os.path.join(self.db_path, f"{db_name}.db")
            if not os.path.exists(source_file):
                return False
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.db_path, "backups", f"{db_name}_{timestamp}.db")
            
            # Copy the database file
            import shutil
            shutil.copy2(source_file, backup_file)
            print(f"Database backed up to: {backup_file}")
            return True
        except Exception as e:
            print(f"Error backing up database: {e}")
            return False

    def restore_database(self, backup_file: str, db_name: str) -> bool:
        """Restore database from backup."""
        try:
            target_file = os.path.join(self.db_path, f"{db_name}.db")
            import shutil
            shutil.copy2(backup_file, target_file)
            print(f"Database restored from: {backup_file}")
            return True
        except Exception as e:
            print(f"Error restoring database: {e}")
            return False

    def get_databases(self) -> List[str]:
        """Get list of available databases."""
        if not os.path.exists(self.db_path):
            return []
        return [f.split(".db")[0] for f in os.listdir(self.db_path) if f.endswith(".db")]

    def get_tables(self) -> List[str]:
        """Get list of tables in current database."""
        if not self.connection or not self.cursor:
            return []
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            return [row[0] for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error fetching tables: {e}")
            return []

    def get_table_data(self, table_name: str, limit: int = 100) -> Tuple[List[str], List[Any]]:
        """Get table data with limit."""
        if not self.connection or not self.cursor:
            return [], []
        try:
            self.cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            if self.cursor.description:
                column_names = [description[0] for description in self.cursor.description]
                results = self.cursor.fetchall()
                return column_names, results
            return [], []
        except sqlite3.Error as e:
            print(f"Error fetching table data: {e}")
            return [], []

    def close_database(self):
        """Close current database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None
            self.current_db = None

    def _split_sql_statements(self, query: str) -> List[str]:
        """Split SQL statements by semicolon, handling strings and comments."""
        statements = []
        current = ""
        in_string = False
        string_char = None
        
        i = 0
        while i < len(query):
            char = query[i]
            
            if not in_string:
                if char in ["'", '"']:
                    in_string = True
                    string_char = char
                    current += char
                elif char == ';':
                    stmt = current.strip()
                    if stmt:
                        statements.append(stmt)
                    current = ""
                else:
                    current += char
            else:
                current += char
                if char == string_char:
                    # Check if it's escaped
                    if i > 0 and query[i-1] == '\\':
                        pass  # Escaped quote, continue
                    else:
                        in_string = False
                        string_char = None
            
            i += 1
        
        # Add the last statement if it exists
        stmt = current.strip()
        if stmt:
            statements.append(stmt)
        
        return statements

    def _extract_database_name(self, query: str) -> Optional[str]:
        """Extract database name from query."""
        import re
        match = re.search(r'(?:CREATE|DROP|USE)\s+(?:DATABASE\s+)?(\w+)', query, re.IGNORECASE)
        return match.group(1) if match else None

    def drop_database(self, db_name: str) -> bool:
        """Drop/delete a database file."""
        db_file = os.path.join(self.db_path, f"{db_name}.db")
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
                return True
            except OSError as e:
                print(f"Error dropping database: {e}")
                return False
        return False

    def save_query_history(self):
        """Save query history to JSON file."""
        try:
            history_file = os.path.join(self.db_path, "query_history.json")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            
            # Create backup of existing file
            if os.path.exists(history_file):
                backup_file = history_file + ".backup"
                import shutil
                shutil.copy2(history_file, backup_file)
            
            # Save to JSON with proper formatting
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.query_history, f, indent=2, ensure_ascii=False)
            
            print(f"Query history saved to: {history_file} ({len(self.query_history)} entries)")
            
        except Exception as e:
            print(f"Error saving query history: {e}")
            # Try to restore from backup if save failed
            try:
                backup_file = history_file + ".backup"
                if os.path.exists(backup_file):
                    import shutil
                    shutil.copy2(backup_file, history_file)
                    print("Restored from backup file")
            except:
                pass

    def load_query_history(self):
        """Load query history from JSON file."""
        try:
            history_file = os.path.join(self.db_path, "query_history.json")
            
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    loaded_history = json.load(f)
                    
                # Validate loaded data
                if isinstance(loaded_history, list):
                    self.query_history = loaded_history
                    print(f"Query history loaded: {len(self.query_history)} entries")
                else:
                    print("Invalid query history format, starting fresh")
                    self.query_history = []
            else:
                print("No query history file found, starting fresh")
                self.query_history = []
                
        except Exception as e:
            print(f"Error loading query history: {e}")
            print("Starting with empty query history")
            self.query_history = []

    def save_favorites(self):
        """Save favorites to JSON file."""
        try:
            favorites_file = os.path.join(self.db_path, "favorites.json")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(favorites_file), exist_ok=True)
            
            # Create backup of existing file
            if os.path.exists(favorites_file):
                backup_file = favorites_file + ".backup"
                import shutil
                shutil.copy2(favorites_file, backup_file)
            
            # Save to JSON with proper formatting
            with open(favorites_file, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, indent=2, ensure_ascii=False)
            
            print(f"Favorites saved to: {favorites_file} ({len(self.favorites)} entries)")
            
        except Exception as e:
            print(f"Error saving favorites: {e}")

    def load_favorites(self):
        """Load favorites from JSON file."""
        try:
            favorites_file = os.path.join(self.db_path, "favorites.json")
            
            if os.path.exists(favorites_file):
                with open(favorites_file, 'r', encoding='utf-8') as f:
                    loaded_favorites = json.load(f)
                    
                # Validate loaded data
                if isinstance(loaded_favorites, list):
                    self.favorites = loaded_favorites
                    print(f"Favorites loaded: {len(self.favorites)} entries")
                else:
                    print("Invalid favorites format, starting fresh")
                    self.favorites = []
            else:
                print("No favorites file found, starting fresh")
                self.favorites = []
                
        except Exception as e:
            print(f"Error loading favorites: {e}")
            print("Starting with empty favorites")
            self.favorites = []

    def save_schemas(self):
        """Save schemas to file."""
        try:
            schemas_file = os.path.join(self.db_path, "schemas", "schemas.json")
            with open(schemas_file, 'w') as f:
                json.dump(self.schemas, f, indent=2)
        except Exception as e:
            print(f"Error saving schemas: {e}")

    def load_schemas(self):
        """Load schemas from file."""
        try:
            schemas_file = os.path.join(self.db_path, "schemas", "schemas.json")
            if os.path.exists(schemas_file):
                with open(schemas_file, 'r') as f:
                    self.schemas = json.load(f)
        except Exception as e:
            print(f"Error loading schemas: {e}")
