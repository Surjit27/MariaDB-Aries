import re
import sqlite3
from typing import List, Dict, Any, Tuple, Optional

class SQLCompiler:
    def __init__(self):
        """Initialize the SQL compiler for converting standard SQL to SQLite-compatible syntax."""
        self.type_mappings = {
            'VARCHAR': 'TEXT',
            'CHAR': 'TEXT',
            'DECIMAL': 'REAL',
            'NUMERIC': 'REAL',
            'FLOAT': 'REAL',
            'DOUBLE': 'REAL',
            'DATE': 'TEXT',
            'DATETIME': 'TEXT',
            'TIMESTAMP': 'TEXT',
            'BOOLEAN': 'INTEGER',
            'TINYINT': 'INTEGER',
            'SMALLINT': 'INTEGER',
            'MEDIUMINT': 'INTEGER',
            'BIGINT': 'INTEGER',
            'INT': 'INTEGER',
            'INTEGER': 'INTEGER',
            'BLOB': 'BLOB'
        }

    def compile_sql(self, sql: str) -> str:
        """Compile standard SQL syntax to SQLite-compatible syntax."""
        # Remove comments
        sql = self._remove_comments(sql)
        
        # Handle CREATE TABLE statements
        if sql.strip().upper().startswith('CREATE TABLE'):
            sql = self._compile_create_table(sql)
        
        # Handle INSERT statements
        elif sql.strip().upper().startswith('INSERT'):
            sql = self._compile_insert(sql)
        
        # Handle other statements (SELECT, UPDATE, DELETE, etc.)
        else:
            sql = self._compile_general_sql(sql)
        
        return sql

    def _remove_comments(self, sql: str) -> str:
        """Remove SQL comments."""
        # Remove single-line comments
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        # Remove multi-line comments
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        return sql

    def _compile_create_table(self, sql: str) -> str:
        """Compile CREATE TABLE statement to SQLite syntax."""
        # Extract table name
        table_match = re.search(r'CREATE\s+TABLE\s+(\w+)', sql, re.IGNORECASE)
        if not table_match:
            return sql
        
        table_name = table_match.group(1)
        
        # Extract column definitions
        columns_match = re.search(r'\((.*)\)', sql, re.DOTALL)
        if not columns_match:
            return sql
        
        columns_text = columns_match.group(1)
        
        # Parse and convert each column
        compiled_columns = []
        column_definitions = self._parse_column_definitions(columns_text)
        
        for col_def in column_definitions:
            compiled_col = self._compile_column_definition(col_def)
            compiled_columns.append(compiled_col)
        
        # Reconstruct the CREATE TABLE statement
        compiled_sql = f"CREATE TABLE {table_name} (\n    " + ",\n    ".join(compiled_columns) + "\n)"
        return compiled_sql

    def _parse_column_definitions(self, columns_text: str) -> List[Dict[str, Any]]:
        """Parse column definitions from CREATE TABLE statement."""
        columns = []
        
        # Simple approach: split by comma and handle each column
        lines = columns_text.split('\n')
        current_col = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this line ends a column definition
            if line.endswith(',') or line.endswith(')'):
                current_col += " " + line
                if line.endswith(','):
                    # Remove trailing comma and parse
                    col_def = current_col.rstrip(',').strip()
                    if col_def:
                        columns.append(self._parse_single_column(col_def))
                    current_col = ""
                elif line.endswith(')'):
                    # This might be the end of the table definition
                    col_def = current_col.rstrip(')').strip()
                    if col_def and not col_def.upper().startswith('PRIMARY KEY'):
                        columns.append(self._parse_single_column(col_def))
                    current_col = ""
            else:
                current_col += " " + line
        
        # Handle any remaining column
        if current_col.strip():
            col_def = current_col.strip()
            if col_def and not col_def.upper().startswith('PRIMARY KEY'):
                columns.append(self._parse_single_column(col_def))
        
        return columns

    def _parse_single_column(self, col_text: str) -> Dict[str, Any]:
        """Parse a single column definition."""
        col_text = col_text.strip()
        
        # Extract column name
        name_match = re.match(r'(\w+)', col_text)
        if not name_match:
            return {'name': '', 'type': 'TEXT', 'constraints': []}
        
        name = name_match.group(1)
        remaining = col_text[len(name):].strip()
        
        # Extract data type with parentheses
        type_match = re.match(r'(\w+)(?:\([^)]*\))?', remaining)
        if type_match:
            data_type = type_match.group(1).upper()
            remaining = remaining[len(type_match.group(0)):].strip()
        else:
            data_type = 'TEXT'
        
        # Map to SQLite type
        sqlite_type = self.type_mappings.get(data_type, 'TEXT')
        
        # Extract constraints
        constraints = []
        constraint_parts = remaining.split()
        i = 0
        while i < len(constraint_parts):
            part = constraint_parts[i].upper()
            if part == 'PRIMARY':
                if i + 1 < len(constraint_parts) and constraint_parts[i + 1].upper() == 'KEY':
                    constraints.extend(['PRIMARY', 'KEY'])
                    i += 1
                else:
                    constraints.append('PRIMARY')
            elif part in ['KEY', 'NOT', 'NULL', 'UNIQUE', 'AUTO_INCREMENT']:
                constraints.append(part)
            i += 1
        
        return {
            'name': name,
            'type': sqlite_type,
            'constraints': constraints
        }

    def _compile_column_definition(self, col_def: Dict[str, Any]) -> str:
        """Compile a single column definition to SQLite syntax."""
        name = col_def['name']
        sqlite_type = col_def['type']
        constraints = col_def['constraints']
        
        # Build the column definition
        result = f"{name} {sqlite_type}"
        
        # Add constraints
        if 'PRIMARY' in constraints and 'KEY' in constraints:
            result += " PRIMARY KEY"
        if 'NOT' in constraints and 'NULL' in constraints:
            result += " NOT NULL"
        if 'UNIQUE' in constraints:
            result += " UNIQUE"
        
        return result

    def _compile_insert(self, sql: str) -> str:
        """Compile INSERT statement to SQLite syntax."""
        # For now, INSERT statements are mostly compatible
        # Just ensure proper date format handling
        sql = re.sub(r"'(\d{4}-\d{2}-\d{2})'", r"'\1'", sql)
        return sql

    def _compile_general_sql(self, sql: str) -> str:
        """Compile general SQL statements."""
        # Handle function name differences
        sql = re.sub(r'\bNOW\(\)\b', "datetime('now')", sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bCURRENT_DATE\b', "date('now')", sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bCURRENT_TIME\b', "time('now')", sql, flags=re.IGNORECASE)
        
        return sql

    def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """Validate SQL syntax and return (is_valid, error_message)."""
        try:
            # Basic syntax validation
            compiled_sql = self.compile_sql(sql)
            
            # Try to parse with sqlite3 (without executing)
            # This is a basic check - in a real implementation, you'd use a proper SQL parser
            if not compiled_sql.strip():
                return False, "Empty SQL statement"
            
            return True, None
        except Exception as e:
            return False, f"SQL validation error: {str(e)}"

    def get_supported_functions(self) -> List[str]:
        """Return list of supported SQL functions."""
        return [
            "COUNT", "SUM", "AVG", "MIN", "MAX",
            "UPPER", "LOWER", "LENGTH", "SUBSTR",
            "datetime", "date", "time", "strftime"
        ]

    def get_supported_types(self) -> Dict[str, str]:
        """Return mapping of supported SQL types to SQLite types."""
        return self.type_mappings.copy()
