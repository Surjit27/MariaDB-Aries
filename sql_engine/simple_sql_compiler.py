import re
from typing import List, Dict, Any, Optional

class SimpleSQLCompiler:
    """Simple SQL compiler to convert standard SQL to SQLite-compatible syntax."""
    
    def __init__(self):
        self.data_type_mappings = {
            'VARCHAR': 'TEXT',
            'CHAR': 'TEXT',
            'NVARCHAR': 'TEXT',
            'NCHAR': 'TEXT',
            'TEXT': 'TEXT',
            'LONGTEXT': 'TEXT',
            'MEDIUMTEXT': 'TEXT',
            'TINYTEXT': 'TEXT',
            'INT': 'INTEGER',
            'INTEGER': 'INTEGER',
            'BIGINT': 'INTEGER',
            'SMALLINT': 'INTEGER',
            'TINYINT': 'INTEGER',
            'MEDIUMINT': 'INTEGER',
            'DECIMAL': 'REAL',
            'NUMERIC': 'REAL',
            'FLOAT': 'REAL',
            'DOUBLE': 'REAL',
            'REAL': 'REAL',
            'DATE': 'TEXT',
            'DATETIME': 'TEXT',
            'TIMESTAMP': 'TEXT',
            'TIME': 'TEXT',
            'YEAR': 'INTEGER',
            'BOOLEAN': 'INTEGER',
            'BOOL': 'INTEGER',
            'BLOB': 'BLOB',
            'LONGBLOB': 'BLOB',
            'MEDIUMBLOB': 'BLOB',
            'TINYBLOB': 'BLOB',
            'BINARY': 'BLOB',
            'VARBINARY': 'BLOB'
        }
        
        self.constraint_mappings = {
            'AUTO_INCREMENT': 'AUTOINCREMENT',
            'AUTO INCREMENT': 'AUTOINCREMENT'
        }
    
    def compile_sql(self, sql: str) -> str:
        """Compile SQL to SQLite-compatible syntax."""
        if not sql or not sql.strip():
            return sql
            
        # Remove comments and normalize whitespace
        sql = self._remove_comments(sql)
        sql = self._normalize_whitespace(sql)
        
        # Handle different SQL statement types
        sql_upper = sql.upper().strip()
        
        if sql_upper.startswith('CREATE TABLE'):
            return self._compile_create_table(sql)
        elif sql_upper.startswith('ALTER TABLE'):
            return self._compile_alter_table(sql)
        elif sql_upper.startswith('INSERT INTO'):
            return self._compile_insert(sql)
        elif sql_upper.startswith('UPDATE'):
            return self._compile_update(sql)
        elif sql_upper.startswith('DELETE FROM'):
            return self._compile_delete(sql)
        elif sql_upper.startswith('SELECT'):
            return self._compile_select(sql)
        elif sql_upper.startswith('USE '):
            # Handle USE statements (database switching)
            return self._compile_use(sql)
        elif sql_upper.startswith('CREATE DATABASE'):
            return self._compile_create_database(sql)
        elif sql_upper.startswith('DROP DATABASE'):
            return self._compile_drop_database(sql)
        else:
            # For other statements, just apply basic transformations
            return self._apply_basic_transformations(sql)
    
    def _remove_comments(self, sql: str) -> str:
        """Remove SQL comments."""
        # Remove single-line comments
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        # Remove multi-line comments
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        return sql
    
    def _normalize_whitespace(self, sql: str) -> str:
        """Normalize whitespace in SQL."""
        # Replace multiple whitespace with single space
        sql = re.sub(r'\s+', ' ', sql)
        # Remove leading/trailing whitespace
        sql = sql.strip()
        return sql
    
    def _compile_create_table(self, sql: str) -> str:
        """Compile CREATE TABLE statement."""
        # Extract table name
        table_match = re.search(r'CREATE\s+TABLE\s+(\w+)', sql, re.IGNORECASE)
        if not table_match:
            return sql
        
        table_name = table_match.group(1)
        
        # Extract column definitions
        columns_match = re.search(r'CREATE\s+TABLE\s+\w+\s*\((.*)\)', sql, re.IGNORECASE | re.DOTALL)
        if not columns_match:
            return sql
        
        columns_text = columns_match.group(1)
        
        # Split columns and constraints
        columns = self._split_columns(columns_text)
        
        # Compile each column
        compiled_columns = []
        foreign_keys = []
        
        for column in columns:
            if self._is_foreign_key_constraint(column):
                foreign_keys.append(column)
            else:
                compiled_column = self._compile_column(column)
                compiled_columns.append(compiled_column)
        
        # Build the compiled SQL
        compiled_sql = f"CREATE TABLE {table_name} (\n"
        compiled_sql += ",\n".join(compiled_columns)
        
        # Add foreign key constraints if any
        if foreign_keys:
            compiled_sql += ",\n" + ",\n".join(foreign_keys)
        
        compiled_sql += "\n)"
        
        return compiled_sql
    
    def _split_columns(self, columns_text: str) -> List[str]:
        """Split column definitions from CREATE TABLE statement."""
        columns = []
        current_column = ""
        paren_count = 0
        
        for char in columns_text:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == ',' and paren_count == 0:
                if current_column.strip():
                    columns.append(current_column.strip())
                current_column = ""
                continue
            
            current_column += char
        
        if current_column.strip():
            columns.append(current_column.strip())
        
        return columns
    
    def _is_foreign_key_constraint(self, column: str) -> bool:
        """Check if a column definition is a foreign key constraint."""
        return 'FOREIGN KEY' in column.upper()
    
    def _compile_column(self, column: str) -> str:
        """Compile a single column definition."""
        # Split column definition into parts
        parts = column.split()
        if not parts:
            return column
        
        column_name = parts[0]
        compiled_parts = [column_name]
        
        # Process data type
        if len(parts) > 1:
            data_type = parts[1].upper()
            # Remove size specifications for SQLite
            data_type = re.sub(r'\(\d+\)', '', data_type)
            data_type = re.sub(r'\(\d+,\s*\d+\)', '', data_type)
            
            # Map to SQLite data type
            if data_type in self.data_type_mappings:
                compiled_parts.append(self.data_type_mappings[data_type])
            else:
                compiled_parts.append(data_type)
        
        # Process constraints
        for i, part in enumerate(parts[2:], 2):
            part_upper = part.upper()
            
            if part_upper in ['PRIMARY', 'KEY']:
                if i < len(parts) - 1 and parts[i + 1].upper() == 'KEY':
                    compiled_parts.append('PRIMARY KEY')
                else:
                    compiled_parts.append('PRIMARY KEY')
            elif part_upper in ['NOT', 'NULL']:
                if i < len(parts) - 1 and parts[i + 1].upper() == 'NULL':
                    compiled_parts.append('NOT NULL')
                else:
                    compiled_parts.append('NOT NULL')
            elif part_upper in ['UNIQUE']:
                compiled_parts.append('UNIQUE')
            elif part_upper in ['AUTO_INCREMENT', 'AUTO', 'INCREMENT']:
                compiled_parts.append('AUTOINCREMENT')
            elif part_upper in ['DEFAULT']:
                # Include default value
                if i < len(parts) - 1:
                    compiled_parts.append('DEFAULT')
                    compiled_parts.append(parts[i + 1])
            elif part_upper not in ['KEY', 'NULL', 'INCREMENT']:
                # Include other constraints
                compiled_parts.append(part)
        
        return ' '.join(compiled_parts)
    
    def _compile_alter_table(self, sql: str) -> str:
        """Compile ALTER TABLE statement."""
        # For now, just return the original SQL
        # SQLite has limited ALTER TABLE support
        return sql
    
    def _compile_insert(self, sql: str) -> str:
        """Compile INSERT statement."""
        return self._apply_basic_transformations(sql)
    
    def _compile_update(self, sql: str) -> str:
        """Compile UPDATE statement."""
        return self._apply_basic_transformations(sql)
    
    def _compile_delete(self, sql: str) -> str:
        """Compile DELETE statement."""
        return self._apply_basic_transformations(sql)
    
    def _compile_select(self, sql: str) -> str:
        """Compile SELECT statement."""
        return self._apply_basic_transformations(sql)
    
    def _compile_use(self, sql: str) -> str:
        """Compile USE statement."""
        # USE statements are handled by the database manager, not SQLite
        return sql
    
    def _compile_create_database(self, sql: str) -> str:
        """Compile CREATE DATABASE statement."""
        # CREATE DATABASE is handled by the database manager, not SQLite
        return sql
    
    def _compile_drop_database(self, sql: str) -> str:
        """Compile DROP DATABASE statement."""
        # DROP DATABASE is handled by the database manager, not SQLite
        return sql
    
    def _apply_basic_transformations(self, sql: str) -> str:
        """Apply basic SQL transformations."""
        # Replace common MySQL/PostgreSQL functions with SQLite equivalents
        sql = re.sub(r'\bLIMIT\s+(\d+)\s+OFFSET\s+(\d+)\b', r'LIMIT \2, \1', sql, flags=re.IGNORECASE)
        
        # Handle string functions
        sql = re.sub(r'\bCONCAT\s*\(', '(', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bIFNULL\s*\(', 'COALESCE(', sql, flags=re.IGNORECASE)
        
        return sql
    
    def validate_sql(self, sql: str) -> Dict[str, Any]:
        """Validate SQL syntax."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        if not sql or not sql.strip():
            result['valid'] = False
            result['errors'].append('Empty SQL statement')
            return result
        
        # Basic syntax validation
        sql_upper = sql.upper().strip()
        
        # Check for balanced parentheses
        if sql.count('(') != sql.count(')'):
            result['warnings'].append('Unbalanced parentheses')
        
        # Check for common syntax issues
        if sql_upper.startswith('CREATE TABLE') and '(' not in sql:
            result['errors'].append('CREATE TABLE statement missing column definitions')
            result['valid'] = False
        
        return result
