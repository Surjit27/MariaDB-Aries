import sqlite3
import os
from typing import List, Dict, Any, Tuple, Optional
from sql_engine.simple_sql_compiler import SimpleSQLCompiler

class DatabaseManager:
    def __init__(self, db_path: str):
        """Initialize the database manager with a path to store SQLite files."""
        self.db_path = db_path
        self.current_db = None
        self.connection = None
        self.cursor = None
        self.sql_compiler = SimpleSQLCompiler()
        # Ensure the database directory exists
        os.makedirs(db_path, exist_ok=True)

    def create_database(self, db_name: str) -> bool:
        """Create a new SQLite database file."""
        db_file = os.path.join(self.db_path, f"{db_name}.db")
        print(f"Creating database: {db_file}")
        print(f"Database path exists: {os.path.exists(self.db_path)}")
        try:
            conn = sqlite3.connect(db_file)
            conn.close()
            print(f"Database created successfully: {db_file}")
            # Automatically open the newly created database
            return self.open_database(db_name)
        except sqlite3.Error as e:
            print(f"Error creating database: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error creating database: {e}")
            return False

    def open_database(self, db_name: str) -> bool:
        """Open an existing SQLite database for operations."""
        db_file = os.path.join(self.db_path, f"{db_name}.db")
        if not os.path.exists(db_file):
            print(f"Database {db_name} does not exist.")
            return False
        try:
            self.connection = sqlite3.connect(db_file)
            self.cursor = self.connection.cursor()
            self.current_db = db_name
            return True
        except sqlite3.Error as e:
            print(f"Error opening database: {e}")
            return False

    def close_database(self) -> None:
        """Close the current database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None
            self.current_db = None

    def execute_query(self, query: str, params: tuple = ()) -> Tuple[List[str], List[Any], Optional[str]]:
        """Execute a SQL query and return column names, results (if applicable), and error message (if any)."""
        query_upper = query.strip().upper()
        
        # Handle CREATE DATABASE command
        if query_upper.startswith("CREATE DATABASE"):
            db_name = self._extract_database_name(query)
            if db_name:
                if self.create_database(db_name):
                    return [], [], None
                else:
                    return [], [], f"Failed to create database '{db_name}'"
            else:
                return [], [], "Invalid CREATE DATABASE syntax"
        
        # Handle USE DATABASE command
        if query_upper.startswith("USE"):
            db_name = self._extract_database_name(query)
            if db_name:
                if self.open_database(db_name):
                    return [], [], None
                else:
                    return [], [], f"Failed to open database '{db_name}'"
            else:
                return [], [], "Invalid USE DATABASE syntax"
        
        # Handle DROP DATABASE command
        if query_upper.startswith("DROP DATABASE"):
            db_name = self._extract_database_name(query)
            if db_name:
                if self.drop_database(db_name):
                    return [], [], None
                else:
                    return [], [], f"Failed to drop database '{db_name}'"
            else:
                return [], [], "Invalid DROP DATABASE syntax"
        
        # For other queries, need an open database
        if not self.connection or not self.cursor:
            return [], [], "No database is currently open. Please create and open a database first using 'CREATE DATABASE dbname;' or the 'Create Database' button."
        
        try:
            # Compile the SQL query to SQLite-compatible syntax
            compiled_query = self.sql_compiler.compile_sql(query)
            print(f"Original query: {query}")
            print(f"Compiled query: {compiled_query}")
            
            self.cursor.execute(compiled_query, params)
            if query_upper.startswith("SELECT"):
                # Fetch column names from cursor description
                column_names = [description[0] for description in self.cursor.description]
                results = self.cursor.fetchall()
                return column_names, results, None
            else:
                self.connection.commit()
                return [], [], None
        except sqlite3.Error as e:
            error_msg = f"Query execution error: {e}"
            print(error_msg)
            return [], [], error_msg

    def get_databases(self) -> List[str]:
        """Return a list of available databases in the storage path."""
        if not os.path.exists(self.db_path):
            return []
        return [f.split(".db")[0] for f in os.listdir(self.db_path) if f.endswith(".db")]

    def get_tables(self) -> List[str]:
        """Return a list of tables in the current database."""
        if not self.connection or not self.cursor:
            return []
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            return [row[0] for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error fetching tables: {e}")
            return []

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Return the schema of a specific table."""
        if not self.connection or not self.cursor:
            return []
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name});")
            return [{"cid": row[0], "name": row[1], "type": row[2], "notnull": row[3], "default": row[4], "pk": row[5]} for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error fetching table schema: {e}")
            return []

    def _extract_database_name(self, query: str) -> Optional[str]:
        """Extract database name from CREATE/DROP DATABASE or USE query."""
        import re
        # Simple regex to extract database name from CREATE DATABASE, DROP DATABASE, or USE
        match = re.search(r'(?:CREATE|DROP)\s+DATABASE\s+(\w+)|USE\s+(\w+)', query, re.IGNORECASE)
        if match:
            return match.group(1) or match.group(2)
        return None

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
    
    def get_columns(self, table_name: str) -> List[Dict[str, str]]:
        """Get column information for a table."""
        if not self.current_db:
            return []
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Convert to list of dictionaries
            column_info = []
            for col in columns:
                column_info.append({
                    'name': col[1],
                    'type': col[2],
                    'not_null': bool(col[3]),
                    'default': col[4],
                    'primary_key': bool(col[5])
                })
            
            return column_info
        except Exception as e:
            print(f"Error getting columns for {table_name}: {e}")
            return []
