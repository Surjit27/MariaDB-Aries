import re
from typing import List, Dict, Any, Optional, Tuple

class SimpleSQLCompiler:
    """Enhanced SQL compiler to convert standard SQL to SQLite-compatible syntax."""
    
    def __init__(self):
        # Data type mappings from various SQL dialects to SQLite
        self.data_type_mappings = {
            # String types
            'VARCHAR': 'TEXT',
            'CHAR': 'TEXT', 
            'NVARCHAR': 'TEXT',
            'NCHAR': 'TEXT',
            'TEXT': 'TEXT',
            'LONGTEXT': 'TEXT',
            'MEDIUMTEXT': 'TEXT',
            'TINYTEXT': 'TEXT',
            'STRING': 'TEXT',
            
            # Integer types
            'INT': 'INTEGER',
            'INTEGER': 'INTEGER',
            'BIGINT': 'INTEGER',
            'SMALLINT': 'INTEGER',
            'TINYINT': 'INTEGER',
            'MEDIUMINT': 'INTEGER',
            'SERIAL': 'INTEGER',
            'BIGSERIAL': 'INTEGER',
            
            # Decimal/Float types
            'DECIMAL': 'REAL',
            'NUMERIC': 'REAL',
            'FLOAT': 'REAL',
            'DOUBLE': 'REAL',
            'REAL': 'REAL',
            'MONEY': 'REAL',
            
            # Date/Time types
            'DATE': 'TEXT',
            'DATETIME': 'TEXT',
            'TIMESTAMP': 'TEXT',
            'TIME': 'TEXT',
            'YEAR': 'INTEGER',
            
            # Boolean types
            'BOOLEAN': 'INTEGER',
            'BOOL': 'INTEGER',
            'BIT': 'INTEGER',
            
            # Binary types
            'BLOB': 'BLOB',
            'LONGBLOB': 'BLOB',
            'MEDIUMBLOB': 'BLOB',
            'TINYBLOB': 'BLOB',
            'BINARY': 'BLOB',
            'VARBINARY': 'BLOB',
            'BYTEA': 'BLOB',
            
            # JSON types
            'JSON': 'TEXT',
            'JSONB': 'TEXT'
        }
        
        # Constraint mappings
        self.constraint_mappings = {
            'AUTO_INCREMENT': 'AUTOINCREMENT',
            'AUTO INCREMENT': 'AUTOINCREMENT',
            'SERIAL': 'AUTOINCREMENT'
        }
        
        # Function mappings
        self.function_mappings = {
            'CONCAT': '||',
            'IFNULL': 'COALESCE',
            'ISNULL': 'COALESCE',
            'LEN': 'LENGTH',
            'SUBSTRING': 'SUBSTR',
            'CHARINDEX': 'INSTR',
            'GETDATE': 'datetime("now")',
            'NOW': 'datetime("now")',
            'CURRENT_TIMESTAMP': 'datetime("now")',
            'CURRENT_DATE': 'date("now")',
            'CURRENT_TIME': 'time("now")'
        }
    
    def compile_sql(self, sql: str) -> str:
        """Compile SQL to SQLite-compatible syntax."""
        if not sql or not sql.strip():
            return sql
            
        # Clean and normalize the SQL
        sql = self._clean_sql(sql)
        
        # Handle different SQL statement types
        sql_upper = sql.upper().strip()
        
        try:
            if sql_upper.startswith('CREATE TABLE'):
                return self._compile_create_table(sql)
            elif sql_upper.startswith('CREATE INDEX'):
                return self._compile_create_index(sql)
            elif sql_upper.startswith('CREATE VIEW'):
                return self._compile_create_view(sql)
            elif sql_upper.startswith('CREATE TRIGGER'):
                return self._compile_create_trigger(sql)
            elif sql_upper.startswith('CREATE FUNCTION'):
                return self._compile_create_function(sql)
            elif sql_upper.startswith('CREATE PROCEDURE'):
                return self._compile_create_procedure(sql)
            elif sql_upper.startswith('CREATE DATABASE'):
                return self._compile_create_database(sql)
            elif sql_upper.startswith('ALTER TABLE'):
                return self._compile_alter_table(sql)
            elif sql_upper.startswith('DROP TABLE'):
                return self._compile_drop_table(sql)
            elif sql_upper.startswith('DROP INDEX'):
                return self._compile_drop_index(sql)
            elif sql_upper.startswith('DROP VIEW'):
                return self._compile_drop_view(sql)
            elif sql_upper.startswith('DROP DATABASE'):
                return self._compile_drop_database(sql)
            elif sql_upper.startswith('INSERT INTO'):
                return self._compile_insert(sql)
            elif sql_upper.startswith('UPDATE'):
                return self._compile_update(sql)
            elif sql_upper.startswith('DELETE FROM'):
                return self._compile_delete(sql)
            elif sql_upper.startswith('SELECT'):
                return self._compile_select(sql)
            elif sql_upper.startswith('USE '):
                return self._compile_use(sql)
            elif sql_upper.startswith('TRUNCATE'):
                return self._compile_truncate(sql)
            elif sql_upper.startswith('EXPLAIN'):
                return self._compile_explain(sql)
            else:
                # For other statements, apply basic transformations
                return self._apply_basic_transformations(sql)
        except Exception as e:
            # If compilation fails, return original SQL
            print(f"Compilation error: {e}")
            return sql
    
    def _clean_sql(self, sql: str) -> str:
        """Clean and normalize SQL."""
        # Remove comments
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        
        # Normalize whitespace
        sql = re.sub(r'\s+', ' ', sql)
        sql = sql.strip()
        
        return sql
    
    def _compile_create_table(self, sql: str) -> str:
        """Compile CREATE TABLE statement."""
        try:
            # Extract table name
            table_match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)', sql, re.IGNORECASE)
            if not table_match:
                return sql
            
            table_name = table_match.group(1)
            
            # Extract column definitions
            columns_match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?\w+\s*\((.*)\)', sql, re.IGNORECASE | re.DOTALL)
            if not columns_match:
                return sql
            
            columns_text = columns_match.group(1).strip()
            
            # Parse columns and constraints
            parsed_items = self._parse_table_definition(columns_text)
            
            # Build compiled SQL
            compiled_sql = f"CREATE TABLE {table_name} (\n"
            
            # Add columns
            column_definitions = []
            for item in parsed_items['columns']:
                column_def = self._compile_column_definition(item)
                if column_def:
                    column_definitions.append(column_def)
            
            # Add constraints
            constraint_definitions = []
            for constraint in parsed_items['constraints']:
                constraint_def = self._compile_constraint(constraint)
                if constraint_def:
                    constraint_definitions.append(constraint_def)
            
            # Combine all definitions
            all_definitions = column_definitions + constraint_definitions
            compiled_sql += ",\n".join(all_definitions)
            compiled_sql += "\n)"
            
            return compiled_sql
            
        except Exception as e:
            print(f"Error compiling CREATE TABLE: {e}")
            return sql
    
    def _parse_table_definition(self, columns_text: str) -> Dict[str, List]:
        """Parse table definition into columns and constraints."""
        columns = []
        constraints = []
        
        # Split by commas, respecting parentheses and quotes
        items = self._split_by_commas(columns_text)
        
        for item in items:
            item = item.strip()
            if not item:
                continue
                
            item_upper = item.upper()
            
            # Check if it's a constraint
            if any(keyword in item_upper for keyword in ['PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE', 'CHECK', 'CONSTRAINT']):
                constraints.append(item)
            else:
                columns.append(item)
        
        return {'columns': columns, 'constraints': constraints}
    
    def _split_by_commas(self, text: str) -> List[str]:
        """Split text by commas, respecting parentheses and quotes."""
        items = []
        current_item = ""
        paren_count = 0
        in_quotes = False
        quote_char = None
        
        for char in text:
            if char in ['"', "'"] and not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
            elif char == '(' and not in_quotes:
                paren_count += 1
            elif char == ')' and not in_quotes:
                paren_count -= 1
            elif char == ',' and paren_count == 0 and not in_quotes:
                if current_item.strip():
                    items.append(current_item.strip())
                current_item = ""
                continue
            
            current_item += char
        
        if current_item.strip():
            items.append(current_item.strip())
        
        return items
    
    def _compile_column_definition(self, column_def: str) -> str:
        """Compile a single column definition."""
        try:
            parts = column_def.split()
            if not parts:
                return column_def
            
            column_name = parts[0]
            compiled_parts = [column_name]
            
            # Process data type
            if len(parts) > 1:
                data_type = parts[1].upper()
                # Remove size specifications
                data_type = re.sub(r'\(\d+(?:,\s*\d+)?\)', '', data_type)
                
                # Map to SQLite data type
                if data_type in self.data_type_mappings:
                    compiled_parts.append(self.data_type_mappings[data_type])
                else:
                    compiled_parts.append(data_type)
            
            # Process constraints
            constraints = self._extract_column_constraints(parts[2:])
            compiled_parts.extend(constraints)
            
            return ' '.join(compiled_parts)
            
        except Exception as e:
            print(f"Error compiling column definition: {e}")
            return column_def
    
    def _extract_column_constraints(self, parts: List[str]) -> List[str]:
        """Extract and compile column constraints."""
        constraints = []
        processed_constraints = set()
        
        i = 0
        while i < len(parts):
            part_upper = parts[i].upper()
            
            if part_upper == 'PRIMARY' and i + 1 < len(parts) and parts[i + 1].upper() == 'KEY':
                if 'PRIMARY KEY' not in processed_constraints:
                    constraints.append('PRIMARY KEY')
                    processed_constraints.add('PRIMARY KEY')
                i += 2
            elif part_upper == 'NOT' and i + 1 < len(parts) and parts[i + 1].upper() == 'NULL':
                if 'NOT NULL' not in processed_constraints:
                    constraints.append('NOT NULL')
                    processed_constraints.add('NOT NULL')
                i += 2
            elif part_upper == 'UNIQUE':
                if 'UNIQUE' not in processed_constraints:
                    constraints.append('UNIQUE')
                    processed_constraints.add('UNIQUE')
                i += 1
            elif part_upper in ['AUTO_INCREMENT', 'AUTO', 'INCREMENT']:
                if 'AUTOINCREMENT' not in processed_constraints:
                    constraints.append('AUTOINCREMENT')
                    processed_constraints.add('AUTOINCREMENT')
                i += 1
            elif part_upper == 'DEFAULT':
                if 'DEFAULT' not in processed_constraints:
                    constraints.append('DEFAULT')
                    if i + 1 < len(parts):
                        constraints.append(parts[i + 1])
                        i += 2
                    else:
                        i += 1
                    processed_constraints.add('DEFAULT')
                else:
                    i += 1
            elif part_upper not in ['KEY', 'NULL', 'INCREMENT', 'PRIMARY', 'NOT']:
                constraints.append(parts[i])
                i += 1
            else:
                i += 1
        
        return ' '.join(compiled_parts)
    
    def _compile_constraint(self, constraint: str) -> str:
        """Compile table constraints."""
        constraint_upper = constraint.upper()
        
        if 'FOREIGN KEY' in constraint_upper:
            return self._compile_foreign_key(constraint)
        elif 'PRIMARY KEY' in constraint_upper:
            return self._compile_primary_key(constraint)
        elif 'UNIQUE' in constraint_upper:
            return self._compile_unique_constraint(constraint)
        elif 'CHECK' in constraint_upper:
            return self._compile_check_constraint(constraint)
        else:
            return constraint
    
    def _compile_foreign_key(self, constraint: str) -> str:
        """Compile foreign key constraint."""
        # Extract foreign key definition
        fk_match = re.search(r'FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+(\w+)\s*\(([^)]+)\)', constraint, re.IGNORECASE)
        if fk_match:
            local_cols = fk_match.group(1)
            ref_table = fk_match.group(2)
            ref_cols = fk_match.group(3)
            return f"FOREIGN KEY ({local_cols}) REFERENCES {ref_table}({ref_cols})"
        return constraint
    
    def _compile_primary_key(self, constraint: str) -> str:
        """Compile primary key constraint."""
        pk_match = re.search(r'PRIMARY\s+KEY\s*\(([^)]+)\)', constraint, re.IGNORECASE)
        if pk_match:
            columns = pk_match.group(1)
            return f"PRIMARY KEY ({columns})"
        return constraint
    
    def _compile_unique_constraint(self, constraint: str) -> str:
        """Compile unique constraint."""
        unique_match = re.search(r'UNIQUE\s*\(([^)]+)\)', constraint, re.IGNORECASE)
        if unique_match:
            columns = unique_match.group(1)
            return f"UNIQUE ({columns})"
        return constraint
    
    def _compile_check_constraint(self, constraint: str) -> str:
        """Compile check constraint."""
        check_match = re.search(r'CHECK\s*\(([^)]+)\)', constraint, re.IGNORECASE)
        if check_match:
            condition = check_match.group(1)
            return f"CHECK ({condition})"
        return constraint
    
    def _compile_create_index(self, sql: str) -> str:
        """Compile CREATE INDEX statement."""
        return self._apply_basic_transformations(sql)
    
    def _compile_create_view(self, sql: str) -> str:
        """Compile CREATE VIEW statement."""
        return self._apply_basic_transformations(sql)
    
    def _compile_create_trigger(self, sql: str) -> str:
        """Compile CREATE TRIGGER statement."""
        return self._apply_basic_transformations(sql)
    
    def _compile_create_function(self, sql: str) -> str:
        """Compile CREATE FUNCTION statement."""
        return self._apply_basic_transformations(sql)
    
    def _compile_create_procedure(self, sql: str) -> str:
        """Compile CREATE PROCEDURE statement."""
        return self._apply_basic_transformations(sql)
    
    def _compile_create_database(self, sql: str) -> str:
        """Compile CREATE DATABASE statement."""
<<<<<<< HEAD
        # Extract database name
        import re
        match = re.search(r'CREATE\s+DATABASE\s+(\w+)', sql, re.IGNORECASE)
        if match:
            db_name = match.group(1)
            return f"-- CREATE DATABASE {db_name}\n-- In SQLite, databases are files. Use the application's database creation feature."
        return sql  # Handled by database manager
    
    def _compile_alter_table(self, sql: str) -> str:
        """Compile ALTER TABLE statement."""
        return self._apply_basic_transformations(sql)
    
    def _compile_drop_table(self, sql: str) -> str:
        """Compile DROP TABLE statement."""
        return self._apply_basic_transformations(sql)
    
    def _compile_drop_index(self, sql: str) -> str:
        """Compile DROP INDEX statement."""
        return self._apply_basic_transformations(sql)
    
    def _compile_drop_view(self, sql: str) -> str:
        """Compile DROP VIEW statement."""
        return self._apply_basic_transformations(sql)
    
    def _compile_drop_database(self, sql: str) -> str:
        """Compile DROP DATABASE statement."""
        return sql  # Handled by database manager
    
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
        return sql  # Handled by database manager
    
    def _compile_truncate(self, sql: str) -> str:
        """Compile TRUNCATE statement."""
        # SQLite doesn't have TRUNCATE, use DELETE instead
        table_match = re.search(r'TRUNCATE\s+(?:TABLE\s+)?(\w+)', sql, re.IGNORECASE)
        if table_match:
            table_name = table_match.group(1)
            return f"DELETE FROM {table_name}"
        return sql
    
    def _compile_explain(self, sql: str) -> str:
        """Compile EXPLAIN statement."""
        return self._apply_basic_transformations(sql)
    
    def _apply_basic_transformations(self, sql: str) -> str:
        """Apply basic SQL transformations."""
        # Replace LIMIT OFFSET syntax
        sql = re.sub(r'\bLIMIT\s+(\d+)\s+OFFSET\s+(\d+)\b', r'LIMIT \2, \1', sql, flags=re.IGNORECASE)
        
        # Replace function calls
        for old_func, new_func in self.function_mappings.items():
            sql = re.sub(rf'\b{old_func}\s*\(', f'{new_func}(', sql, flags=re.IGNORECASE)
        
        # Handle string concatenation
        sql = re.sub(r'\bCONCAT\s*\(', '(', sql, flags=re.IGNORECASE)
        
        # Replace data types in function parameters
        for old_type, new_type in self.data_type_mappings.items():
            sql = re.sub(rf'\b{old_type}\s*\(\d+\)', new_type, sql, flags=re.IGNORECASE)
        
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
        
        # Check for balanced quotes
        single_quotes = sql.count("'")
        double_quotes = sql.count('"')
        if single_quotes % 2 != 0:
            result['warnings'].append('Unbalanced single quotes')
        if double_quotes % 2 != 0:
            result['warnings'].append('Unbalanced double quotes')
        
        # Check for common syntax issues
        if sql_upper.startswith('CREATE TABLE') and '(' not in sql:
            result['errors'].append('CREATE TABLE statement missing column definitions')
            result['valid'] = False
        
        # Check for semicolon at end
        if not sql.strip().endswith(';') and not sql_upper.startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE')):
            result['warnings'].append('Statement should end with semicolon')
        
        return result