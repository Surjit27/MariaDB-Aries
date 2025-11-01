import re
from typing import List, Dict, Any, Optional, Tuple

class SimpleSQLCompiler:
    """Enhanced SQL compiler to convert standard SQL to SQLite-compatible syntax."""
    
    def __init__(self):
        # Data type mappings from various SQL dialects to SQLite
        self.data_type_mappings = {
            # String types - MySQL
            'VARCHAR': 'TEXT',
            'CHAR': 'TEXT', 
            'NVARCHAR': 'TEXT',
            'NCHAR': 'TEXT',
            'TEXT': 'TEXT',
            'LONGTEXT': 'TEXT',
            'MEDIUMTEXT': 'TEXT',
            'TINYTEXT': 'TEXT',
            'STRING': 'TEXT',
            # PostgreSQL
            'CHARACTER': 'TEXT',
            'CHARACTER VARYING': 'TEXT',
            'CHARACTER VARYING': 'TEXT',
            # SQL Server
            'NCHAR': 'TEXT',
            'NVARCHAR': 'TEXT',
            'NTEXT': 'TEXT',
            'XML': 'TEXT',
            # Oracle
            'LONG': 'TEXT',
            'CLOB': 'TEXT',
            'NCLOB': 'TEXT',
            # Misc
            'ENUM': 'TEXT',
            'SET': 'TEXT',
            
            # Integer types
            'INT': 'INTEGER',
            'INTEGER': 'INTEGER',
            'BIGINT': 'INTEGER',
            'SMALLINT': 'INTEGER',
            'TINYINT': 'INTEGER',
            'MEDIUMINT': 'INTEGER',
            'SERIAL': 'INTEGER',
            'BIGSERIAL': 'INTEGER',
            # PostgreSQL
            'SMALLSERIAL': 'INTEGER',
            'SERIAL4': 'INTEGER',
            'BIGSERIAL8': 'INTEGER',
            # Oracle
            'NUMBER': 'INTEGER',  # When used without decimals
            # SQL Server
            'BIGINT': 'INTEGER',
            'SMALLINT': 'INTEGER',
            'TINYINT': 'INTEGER',
            
            # Decimal/Float types
            'DECIMAL': 'REAL',
            'NUMERIC': 'REAL',
            'FLOAT': 'REAL',
            'DOUBLE': 'REAL',
            'DOUBLE PRECISION': 'REAL',
            'REAL': 'REAL',
            'MONEY': 'REAL',
            'SMALLMONEY': 'REAL',  # SQL Server
            'FLOAT4': 'REAL',  # PostgreSQL
            'FLOAT8': 'REAL',  # PostgreSQL
            'NUMBER': 'REAL',  # Oracle (with decimals)
            
            # Date/Time types
            'DATE': 'TEXT',
            'DATETIME': 'TEXT',
            'DATETIME2': 'TEXT',  # SQL Server
            'SMALLDATETIME': 'TEXT',  # SQL Server
            'TIMESTAMP': 'TEXT',
            'TIME': 'TEXT',
            'TIMETZ': 'TEXT',  # PostgreSQL
            'TIMESTAMPTZ': 'TEXT',  # PostgreSQL
            'INTERVAL': 'TEXT',  # PostgreSQL
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
            'BYTEA': 'BLOB',  # PostgreSQL
            'IMAGE': 'BLOB',  # SQL Server
            'RAW': 'BLOB',  # Oracle
            'LONG RAW': 'BLOB',  # Oracle
            
            # JSON types
            'JSON': 'TEXT',
            'JSONB': 'TEXT',  # PostgreSQL
            
            # UUID (PostgreSQL)
            'UUID': 'TEXT',
            
            # Array types (PostgreSQL) - store as TEXT
            'ARRAY': 'TEXT',
            
            # Geographic types (PostGIS) - store as TEXT/BLOB
            'POINT': 'TEXT',
            'GEOMETRY': 'TEXT',
            'GEOGRAPHY': 'TEXT'
        }
        
        # Constraint mappings
        self.constraint_mappings = {
            'AUTO_INCREMENT': 'AUTOINCREMENT',
            'AUTO INCREMENT': 'AUTOINCREMENT',
            'SERIAL': 'AUTOINCREMENT'
        }
        
        # Function mappings from various SQL dialects
        self.function_mappings = {
            # String functions
            'CONCAT': '||',  # MySQL - convert to concatenation operator
            'CONCAT_WS': '||',  # MySQL
            'IFNULL': 'COALESCE',  # MySQL/SQLite
            'ISNULL': 'COALESCE',  # SQL Server
            'NVL': 'COALESCE',  # Oracle
            'NVL2': 'COALESCE',  # Oracle
            'LEN': 'LENGTH',  # SQL Server
            'SUBSTRING': 'SUBSTR',  # Standard -> SQLite
            'SUBSTR': 'SUBSTR',  # SQLite
            'LEFT': 'SUBSTR',  # MySQL/SQL Server
            'RIGHT': 'SUBSTR',  # MySQL/SQL Server
            'CHARINDEX': 'INSTR',  # SQL Server
            'LOCATE': 'INSTR',  # MySQL
            'POSITION': 'INSTR',  # PostgreSQL
            'STRPOS': 'INSTR',  # PostgreSQL
            'REPLACE': 'REPLACE',  # Keep as is
            'UPPER': 'UPPER',  # Standard
            'LOWER': 'LOWER',  # Standard
            'LTRIM': 'LTRIM',  # Standard
            'RTRIM': 'RTRIM',  # Standard
            'TRIM': 'TRIM',  # Standard
            'LPAD': 'PRINTF',  # MySQL - approximate
            'RPAD': 'PRINTF',  # MySQL - approximate
            'SPACE': '',  # SQL Server - remove or replace
            'REPLICATE': 'REPLACE',  # SQL Server
            'REVERSE': 'REVERSE',  # SQL Server/MySQL
            'SOUNDEX': 'SOUNDEX',  # SQL Server - SQLite has it
            
            # Date/Time functions
            'GETDATE': 'datetime("now")',  # SQL Server
            'GETUTCDATE': 'datetime("now", "utc")',  # SQL Server
            'NOW': 'datetime("now")',  # MySQL
            'CURRENT_TIMESTAMP': 'datetime("now")',  # Standard
            'CURRENT_DATE': 'date("now")',  # Standard
            'CURRENT_TIME': 'time("now")',  # Standard
            'SYSDATE': 'datetime("now")',  # Oracle
            'SYSTIMESTAMP': 'datetime("now")',  # Oracle
            'CURRENT_TIMESTAMP': 'datetime("now")',  # PostgreSQL
            'LOCALTIMESTAMP': 'datetime("now")',  # PostgreSQL
            'DATEADD': 'datetime',  # SQL Server - approximate
            'DATEDIFF': 'julianday',  # SQL Server - approximate
            'DATEPART': 'strftime',  # SQL Server - approximate
            'DATENAME': 'strftime',  # SQL Server - approximate
            'YEAR': 'strftime("%Y", ...)',  # MySQL/SQL Server
            'MONTH': 'strftime("%m", ...)',  # MySQL/SQL Server
            'DAY': 'strftime("%d", ...)',  # MySQL/SQL Server
            'DAYOFMONTH': 'strftime("%d", ...)',  # MySQL
            'DAYOFWEEK': 'strftime("%w", ...)',  # MySQL
            'DAYOFYEAR': 'strftime("%j", ...)',  # MySQL
            'HOUR': 'strftime("%H", ...)',  # MySQL
            'MINUTE': 'strftime("%M", ...)',  # MySQL
            'SECOND': 'strftime("%S", ...)',  # MySQL
            'EXTRACT': 'strftime',  # Standard - approximate
            'DATE_FORMAT': 'strftime',  # MySQL - approximate
            'TO_DATE': 'date',  # Oracle
            'TO_TIMESTAMP': 'datetime',  # Oracle/PostgreSQL
            'TO_CHAR': 'strftime',  # Oracle - approximate
            
            # Numeric functions
            'ABS': 'ABS',
            'CEIL': 'CEIL',
            'CEILING': 'CEIL',
            'FLOOR': 'FLOOR',
            'ROUND': 'ROUND',
            'TRUNC': 'ROUND',  # Oracle - approximate
            'TRUNCATE': 'ROUND',  # MySQL - approximate
            'POWER': 'POWER',
            'SQRT': 'SQRT',
            'RAND': 'RANDOM',  # SQL Server -> SQLite
            'RANDOM': 'RANDOM',  # PostgreSQL/SQLite
            'NEWID': 'RANDOM',  # SQL Server
            'SIGN': 'SIGN',  # Standard
            'MOD': '%',  # Standard
            'PI': '3.141592653589793',  # Constant
            
            # Aggregate functions
            'COUNT': 'COUNT',
            'SUM': 'SUM',
            'AVG': 'AVG',
            'MIN': 'MIN',
            'MAX': 'MAX',
            'STDDEV': 'STDEV',  # Oracle
            'STDDEV_POP': 'STDEV',  # PostgreSQL
            'VARIANCE': 'VAR',  # Oracle
            
            # Conditional functions
            'IIF': 'CASE WHEN ... THEN ... ELSE ... END',  # SQL Server
            'IF': 'CASE WHEN ... THEN ... ELSE ... END',  # MySQL
            'DECODE': 'CASE WHEN ... THEN ... ELSE ... END',  # Oracle
            'NULLIF': 'NULLIF',  # Standard
            
            # Type conversion
            'CAST': 'CAST',
            'CONVERT': 'CAST',  # SQL Server -> CAST
            'TO_NUMBER': 'CAST(... AS NUMERIC)',  # Oracle
            'TO_CHAR': 'CAST(... AS TEXT)',  # Oracle
            
            # Other functions
            'COALESCE': 'COALESCE',
            'ISNULL': 'COALESCE',  # SQL Server
            'NULLIF': 'NULLIF',
            'GREATEST': 'MAX',  # MySQL/PostgreSQL
            'LEAST': 'MIN',  # MySQL/PostgreSQL
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
            # Handle COMMENT ON statements (SQLite doesn't support - ignore them)
            if sql_upper.startswith('COMMENT ON'):
                return ''  # Return empty string to skip execution
            
            # Handle CREATE OR REPLACE statements
            if sql_upper.startswith('CREATE OR REPLACE VIEW'):
                return self._compile_create_or_replace_view(sql)
            elif sql_upper.startswith('CREATE OR REPLACE TRIGGER'):
                return self._compile_create_or_replace_trigger(sql)
            elif sql_upper.startswith('CREATE OR REPLACE FUNCTION'):
                return self._compile_create_or_replace_function(sql)
            elif sql_upper.startswith('CREATE OR REPLACE INDEX'):
                return self._compile_create_or_replace_index(sql)
            elif sql_upper.startswith('CREATE TABLE'):
                # Automatically add IF NOT EXISTS if not present (to handle existing tables gracefully)
                if 'IF NOT EXISTS' not in sql_upper:
                    sql = re.sub(r'CREATE\s+TABLE\s+(\w+)', r'CREATE TABLE IF NOT EXISTS \1', sql, flags=re.IGNORECASE)
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
            elif sql_upper.startswith('MERGE'):
                return self._compile_merge(sql)
            elif sql_upper.startswith('UPSERT'):
                return self._compile_upsert(sql)
            elif sql_upper.startswith('WITH'):
                return self._compile_with_cte(sql)
            elif sql_upper.startswith('BEGIN'):
                return self._compile_transaction(sql)
            elif sql_upper.startswith('COMMIT'):
                return self._compile_commit(sql)
            elif sql_upper.startswith('ROLLBACK'):
                return self._compile_rollback(sql)
            elif sql_upper.startswith('SAVEPOINT'):
                return self._compile_savepoint(sql)
            elif sql_upper.startswith('RELEASE'):
                return self._compile_release_savepoint(sql)
            else:
                # For other statements, apply basic transformations
                return self._apply_basic_transformations(sql)
        except Exception as e:
            # If compilation fails, return original SQL
            print(f"Compilation error: {e}")
            return sql
    
    def _clean_sql(self, sql: str) -> str:
        """Clean and normalize SQL."""
        # Preserve line structure for better parsing, but remove excessive whitespace
        lines = sql.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove single-line comments
            line = re.sub(r'--.*$', '', line)
            # Remove trailing whitespace
            line = line.rstrip()
            if line.strip():  # Keep non-empty lines
                cleaned_lines.append(line)
        
        sql = '\n'.join(cleaned_lines)
        
        # Remove multi-line comments
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        
        # Normalize excessive whitespace (but preserve single spaces)
        sql = re.sub(r'[ \t]+', ' ', sql)  # Multiple spaces/tabs to single space
        sql = re.sub(r'\n\s*\n', '\n', sql)  # Multiple newlines to single
        
        sql = sql.strip()
        
        return sql
    
    def _compile_create_table(self, sql: str) -> str:
        """Compile CREATE TABLE statement."""
        try:
            # Check for IF NOT EXISTS
            has_if_not_exists = bool(re.search(r'CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS', sql, re.IGNORECASE))
            
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
            
            # Build compiled SQL with IF NOT EXISTS if present
            if_not_exists_clause = " IF NOT EXISTS" if has_if_not_exists else ""
            compiled_sql = f"CREATE TABLE{if_not_exists_clause} {table_name} (\n"
            
            # Add columns
            column_definitions = []
            column_names = set()  # Track column names to detect duplicates
            columns_with_primary_key = set()  # Track columns that have PRIMARY KEY inline
            
            for item in parsed_items['columns']:
                column_def = self._compile_column_definition(item)
                if column_def:
                    # Extract column name from compiled definition (first word)
                    col_name_match = re.match(r'^(\w+)', column_def.strip())
                    if col_name_match:
                        col_name = col_name_match.group(1)
                        if col_name in column_names:
                            print(f"Warning: Duplicate column name '{col_name}' detected in CREATE TABLE {table_name}")
                            # Skip duplicate column
                            continue
                        column_names.add(col_name)
                        
                        # Check if this column has PRIMARY KEY inline
                        if 'PRIMARY KEY' in column_def.upper():
                            columns_with_primary_key.add(col_name)
                    
                    column_definitions.append(column_def)
            
            # Add constraints - skip PRIMARY KEY constraints that are redundant
            constraint_definitions = []
            for constraint in parsed_items['constraints']:
                constraint_upper = constraint.upper()
                
                # Check if this is a PRIMARY KEY constraint that might be redundant
                if 'PRIMARY KEY' in constraint_upper:
                    # Extract column names from PRIMARY KEY constraint
                    pk_match = re.search(r'PRIMARY\s+KEY\s*\(([^)]+)\)', constraint, re.IGNORECASE)
                    if pk_match:
                        pk_columns = [col.strip() for col in pk_match.group(1).split(',')]
                        # If it's a single column PK and that column already has PRIMARY KEY inline, skip it
                        if len(pk_columns) == 1 and pk_columns[0] in columns_with_primary_key:
                            print(f"Warning: Skipping redundant PRIMARY KEY constraint for column '{pk_columns[0]}' (already defined inline)")
                            continue
                
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
            
            # Check if it's a standalone constraint (not inline with column definition)
            # Standalone constraints typically start with CONSTRAINT keyword or are PRIMARY KEY/FOREIGN KEY without column name before them
            is_standalone_constraint = (
                item_upper.startswith('CONSTRAINT') or
                item_upper.startswith('PRIMARY KEY') or
                (item_upper.startswith('FOREIGN KEY') and not re.match(r'^\w+\s+FOREIGN\s+KEY', item, re.IGNORECASE)) or
                (item_upper.startswith('UNIQUE') and '(' in item and not re.match(r'^\w+\s+UNIQUE', item, re.IGNORECASE)) or
                item_upper.startswith('CHECK')
            )
            
            if is_standalone_constraint:
                constraints.append(item)
            else:
                # This is a column definition (may contain inline constraints like PRIMARY KEY)
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
            # First, extract column name (first word before space or parenthesis)
            name_match = re.match(r'^(\w+)', column_def.strip())
            if not name_match:
                return column_def
            
            column_name = name_match.group(1)
            remaining = column_def[len(column_name):].strip()
            
            compiled_parts = [column_name]
            
            # Check if this column has AUTO_INCREMENT and PRIMARY KEY (needs INTEGER type)
            has_auto_increment = 'AUTO_INCREMENT' in remaining.upper() or 'AUTO INCREMENT' in remaining.upper()
            has_primary_key = 'PRIMARY KEY' in remaining.upper()
            needs_integer_for_autoincrement = has_auto_increment and has_primary_key
            
            # Process data type (handle ENUM specially)
            enum_match = re.search(r'ENUM\s*\(([^)]+)\)', remaining, re.IGNORECASE)
            if enum_match:
                # Extract ENUM values
                enum_values = enum_match.group(1)
                # Convert ENUM to TEXT
                compiled_parts.append('TEXT')
                # Remove ENUM(...) from remaining
                remaining = remaining[:enum_match.start()] + remaining[enum_match.end():]
                # Could add CHECK constraint here, but for simplicity we'll just use TEXT
            else:
                # Extract data type (first word after column name)
                type_match = re.match(r'^(\w+(?:\s+\(\s*\d+(?:\s*,\s*\d+)?\s*\))?)', remaining, re.IGNORECASE)
                if type_match:
                    data_type_full = type_match.group(1)
                    data_type = data_type_full.split('(')[0].upper()
                    
                    # If AUTO_INCREMENT with PRIMARY KEY, force INTEGER type (SQLite requirement)
                    if needs_integer_for_autoincrement:
                        compiled_parts.append('INTEGER')
                    else:
                        # Map to SQLite data type (SQLite ignores size specifications)
                        # Remove size specifications like (50) or (4,1) - they're already removed from data_type
                        data_type_base = data_type
                        
                        # Map to SQLite data type
                        if data_type_base in self.data_type_mappings:
                            compiled_parts.append(self.data_type_mappings[data_type_base])
                        else:
                            # For unknown types, use TEXT or INTEGER
                            if data_type_base in ['INT', 'INTEGER', 'BIGINT', 'SMALLINT', 'TINYINT']:
                                compiled_parts.append('INTEGER')
                            else:
                                compiled_parts.append('TEXT')
                    
                    # Remove the data type from remaining
                    remaining = remaining[len(data_type_full):].strip()
                elif needs_integer_for_autoincrement:
                    # No explicit type, but needs INTEGER for AUTOINCREMENT
                    compiled_parts.append('INTEGER')
            
            # Parse remaining constraints
            if remaining:
                # Split by spaces but be careful with parentheses
                constraint_parts = []
                current_part = ""
                paren_level = 0
                
                i = 0
                while i < len(remaining):
                    char = remaining[i]
                    if char == '(':
                        paren_level += 1
                        current_part += char
                    elif char == ')':
                        paren_level -= 1
                        current_part += char
                    elif char == ' ' and paren_level == 0:
                        if current_part.strip():
                            constraint_parts.append(current_part.strip())
                        current_part = ""
                    else:
                        current_part += char
                    i += 1
                
                if current_part.strip():
                    constraint_parts.append(current_part.strip())
                
                # Process constraints
                constraints = self._extract_column_constraints(constraint_parts)
                compiled_parts.extend(constraints)
            
            # Join and clean up - remove any size specifications like (100) from the output
            result = ' '.join(compiled_parts)
            # Remove size specifications like TEXT (100) -> TEXT, INTEGER (10) -> INTEGER
            result = re.sub(r'\s+\(\s*\d+(?:\s*,\s*\d+)?\s*\)', '', result)
            
            return result
            
        except Exception as e:
            print(f"Error compiling column definition: {e}")
            import traceback
            traceback.print_exc()
            return column_def
    
    def _extract_column_constraints(self, parts: List[str]) -> List[str]:
        """Extract and compile column constraints.
        Important: In SQLite, AUTOINCREMENT must come AFTER PRIMARY KEY when both are present.
        """
        constraints = []
        processed_constraints = set()
        has_primary_key = False
        has_autoincrement = False
        
        i = 0
        while i < len(parts):
            part_upper = parts[i].upper()
            
            if part_upper == 'PRIMARY' and i + 1 < len(parts) and parts[i + 1].upper() == 'KEY':
                if 'PRIMARY KEY' not in processed_constraints:
                    constraints.append('PRIMARY KEY')
                    processed_constraints.add('PRIMARY KEY')
                    has_primary_key = True
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
                    # Don't add yet - we'll add it after PRIMARY KEY if present
                    has_autoincrement = True
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
            elif part_upper not in ['KEY', 'NULL', 'INCREMENT', 'PRIMARY', 'NOT', 'AUTO']:
                constraints.append(parts[i])
                i += 1
            else:
                i += 1
        
        # Add AUTOINCREMENT after PRIMARY KEY if both are present (SQLite requirement)
        if has_autoincrement and has_primary_key:
            # Find PRIMARY KEY and insert AUTOINCREMENT right after it
            for idx, constraint in enumerate(constraints):
                if constraint == 'PRIMARY KEY':
                    constraints.insert(idx + 1, 'AUTOINCREMENT')
                    break
        elif has_autoincrement:
            # Just add AUTOINCREMENT at the end if no PRIMARY KEY
            constraints.append('AUTOINCREMENT')
        
        return constraints
    
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
    
    def _compile_create_or_replace_index(self, sql: str) -> str:
        """Compile CREATE OR REPLACE INDEX to SQLite syntax (DROP INDEX IF EXISTS then CREATE INDEX)."""
        import re
        
        # Extract index name (handle public.schema format and UNIQUE keyword)
        index_match = re.search(r'CREATE\s+OR\s+REPLACE\s+(?:UNIQUE\s+)?INDEX\s+(?:public\.)?(\w+)', sql, re.IGNORECASE)
        if not index_match:
            return sql
        
        index_name = index_match.group(1)
        
        # Check if UNIQUE
        is_unique = 'UNIQUE' in sql.upper()
        
        # Extract the rest of the statement (everything after index name)
        rest_match = re.search(r'CREATE\s+OR\s+REPLACE\s+(?:UNIQUE\s+)?INDEX\s+(?:public\.)?\w+\s+(.*)$', sql, re.IGNORECASE | re.DOTALL)
        if not rest_match:
            return sql
        
        rest_part = rest_match.group(1).strip()
        
        # Remove public. prefixes from table names
        rest_part = re.sub(r'\bON\s+public\.(\w+)', r'ON \1', rest_part, flags=re.IGNORECASE)
        
        # Remove trailing semicolon if present
        rest_part = rest_part.rstrip(';').strip()
        
        # Create SQLite-compatible statements: DROP INDEX IF EXISTS then CREATE INDEX
        drop_statement = f"DROP INDEX IF EXISTS {index_name};"
        unique_keyword = "UNIQUE " if is_unique else ""
        create_statement = f"CREATE {unique_keyword}INDEX {index_name} {rest_part}"
        
        return f"{drop_statement}\n{create_statement}"
    
    def _compile_create_index(self, sql: str) -> str:
        """Compile CREATE INDEX statement."""
        import re
        # Remove public. schema prefix from index name
        sql = re.sub(r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:public\.)?', lambda m: m.group(0).replace('public.', ''), sql, flags=re.IGNORECASE)
        # Remove public. prefixes from table names
        sql = re.sub(r'\bON\s+public\.(\w+)', r'ON \1', sql, flags=re.IGNORECASE)
        return self._apply_basic_transformations(sql)
    
    def _compile_create_or_replace_view(self, sql: str) -> str:
        """Compile CREATE OR REPLACE VIEW to SQLite syntax (DROP VIEW IF EXISTS then CREATE VIEW)."""
        import re
        
        # Extract view name (handle public.schema format)
        view_match = re.search(r'CREATE\s+OR\s+REPLACE\s+VIEW\s+(?:public\.)?(\w+)', sql, re.IGNORECASE)
        if not view_match:
            return sql
        
        view_name = view_match.group(1)
        
        # Extract the SELECT part (everything after AS)
        as_match = re.search(r'\bAS\s+(.*)$', sql, re.IGNORECASE | re.DOTALL)
        if not as_match:
            return sql
        
        select_part = as_match.group(1).strip()
        
        # Remove public. prefixes from table names in SELECT
        select_part = re.sub(r'\bpublic\.(\w+)', r'\1', select_part, flags=re.IGNORECASE)
        
        # Remove trailing semicolon if present
        select_part = select_part.rstrip(';').strip()
        
        # Create SQLite-compatible statements: DROP VIEW IF EXISTS then CREATE VIEW
        drop_statement = f"DROP VIEW IF EXISTS {view_name};"
        create_statement = f"CREATE VIEW {view_name} AS {select_part}"
        
        return f"{drop_statement}\n{create_statement}"
    
    def _compile_create_view(self, sql: str) -> str:
        """Compile CREATE VIEW statement."""
        import re
        
        # Remove public. schema prefix from view name
        sql = re.sub(r'CREATE\s+VIEW\s+(?:public\.)?', 'CREATE VIEW ', sql, flags=re.IGNORECASE)
        
        # Remove public. prefixes from table names in SELECT
        sql = re.sub(r'\bpublic\.(\w+)', r'\1', sql, flags=re.IGNORECASE)
        
        return self._apply_basic_transformations(sql)
    
    def _compile_create_or_replace_trigger(self, sql: str) -> str:
        """Compile CREATE OR REPLACE TRIGGER to SQLite syntax (DROP TRIGGER IF EXISTS then CREATE TRIGGER)."""
        import re
        
        # Extract trigger name (handle public.schema format)
        trigger_match = re.search(r'CREATE\s+OR\s+REPLACE\s+TRIGGER\s+(?:public\.)?(\w+)', sql, re.IGNORECASE)
        if not trigger_match:
            return sql
        
        trigger_name = trigger_match.group(1)
        
        # Extract the rest of the statement (everything after trigger name)
        rest_match = re.search(r'CREATE\s+OR\s+REPLACE\s+TRIGGER\s+(?:public\.)?\w+\s+(.*)$', sql, re.IGNORECASE | re.DOTALL)
        if not rest_match:
            return sql
        
        rest_part = rest_match.group(1).strip()
        
        # Remove public. prefixes from table names
        rest_part = re.sub(r'\bON\s+public\.(\w+)', r'ON \1', rest_part, flags=re.IGNORECASE)
        
        # Remove trailing semicolon if present
        rest_part = rest_part.rstrip(';').strip()
        
        # Create SQLite-compatible statements: DROP TRIGGER IF EXISTS then CREATE TRIGGER
        drop_statement = f"DROP TRIGGER IF EXISTS {trigger_name};"
        create_statement = f"CREATE TRIGGER {trigger_name} {rest_part}"
        
        return f"{drop_statement}\n{create_statement}"
    
    def _compile_create_trigger(self, sql: str) -> str:
        """Compile CREATE TRIGGER statement."""
        import re
        # Remove public. schema prefix from trigger name
        sql = re.sub(r'CREATE\s+TRIGGER\s+(?:public\.)?', 'CREATE TRIGGER ', sql, flags=re.IGNORECASE)
        # Remove public. prefixes from table names
        sql = re.sub(r'\bON\s+public\.(\w+)', r'ON \1', sql, flags=re.IGNORECASE)
        return self._apply_basic_transformations(sql)
    
    def _compile_create_or_replace_function(self, sql: str) -> str:
        """Compile CREATE OR REPLACE FUNCTION to SQLite syntax (DROP FUNCTION IF EXISTS then CREATE FUNCTION)."""
        import re
        
        # Extract function name (handle public.schema format)
        func_match = re.search(r'CREATE\s+OR\s+REPLACE\s+FUNCTION\s+(?:public\.)?(\w+)', sql, re.IGNORECASE)
        if not func_match:
            return sql
        
        func_name = func_match.group(1)
        
        # For SQLite, functions are usually not stored - return a comment
        # But we'll compile it anyway in case the user wants to track it
        drop_statement = f"-- DROP FUNCTION IF EXISTS {func_name}; -- Not supported in SQLite"
        create_statement = f"-- {sql.replace('CREATE OR REPLACE FUNCTION', 'CREATE FUNCTION').replace('CREATE OR REPLACE', 'CREATE')}"
        
        return f"{drop_statement}\n{create_statement}"
    
    def _compile_create_function(self, sql: str) -> str:
        """Compile CREATE FUNCTION statement."""
        import re
        # Remove public. schema prefix from function name
        sql = re.sub(r'CREATE\s+FUNCTION\s+(?:public\.)?', 'CREATE FUNCTION ', sql, flags=re.IGNORECASE)
        return self._apply_basic_transformations(sql)
    
    def _compile_create_procedure(self, sql: str) -> str:
        """Compile CREATE PROCEDURE statement."""
        import re
        # Remove public. schema prefix from procedure name
        sql = re.sub(r'CREATE\s+PROCEDURE\s+(?:public\.)?', 'CREATE PROCEDURE ', sql, flags=re.IGNORECASE)
        return self._apply_basic_transformations(sql)
    
    def _compile_create_database(self, sql: str) -> str:
        """Compile CREATE DATABASE statement."""
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
    
    def _compile_upsert(self, sql: str) -> str:
        """Compile UPSERT statement to INSERT OR REPLACE."""
        import re
        # UPSERT is PostgreSQL syntax, SQLite uses INSERT OR REPLACE
        sql = re.sub(r'\bUPSERT\b', 'INSERT OR REPLACE', sql, flags=re.IGNORECASE)
        return self._apply_basic_transformations(sql)
    
    def _compile_with_cte(self, sql: str) -> str:
        """Compile WITH CTE (Common Table Expression) - SQLite supports this."""
        # SQLite 3.8.3+ supports CTEs, just apply transformations
        return self._apply_basic_transformations(sql)
    
    def _compile_transaction(self, sql: str) -> str:
        """Compile BEGIN TRANSACTION."""
        import re
        # SQLite supports BEGIN TRANSACTION
        sql = re.sub(r'\bBEGIN\s+TRANSACTION\b', 'BEGIN TRANSACTION', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bBEGIN\s+WORK\b', 'BEGIN TRANSACTION', sql, flags=re.IGNORECASE)
        return sql
    
    def _compile_commit(self, sql: str) -> str:
        """Compile COMMIT statement."""
        import re
        sql = re.sub(r'\bCOMMIT\s+TRANSACTION\b', 'COMMIT', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bCOMMIT\s+WORK\b', 'COMMIT', sql, flags=re.IGNORECASE)
        return sql
    
    def _compile_rollback(self, sql: str) -> str:
        """Compile ROLLBACK statement."""
        import re
        sql = re.sub(r'\bROLLBACK\s+TRANSACTION\b', 'ROLLBACK', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bROLLBACK\s+WORK\b', 'ROLLBACK', sql, flags=re.IGNORECASE)
        return sql
    
    def _compile_savepoint(self, sql: str) -> str:
        """Compile SAVEPOINT statement - SQLite supports this."""
        return self._apply_basic_transformations(sql)
    
    def _compile_release_savepoint(self, sql: str) -> str:
        """Compile RELEASE SAVEPOINT statement - SQLite supports this."""
        return self._apply_basic_transformations(sql)
    
    def _apply_basic_transformations(self, sql: str) -> str:
        """Apply basic SQL transformations."""
        import re
        
        # Replace LIMIT OFFSET syntax (MySQL/PostgreSQL -> SQLite)
        sql = re.sub(r'\bLIMIT\s+(\d+)\s+OFFSET\s+(\d+)\b', r'LIMIT \2, \1', sql, flags=re.IGNORECASE)
        # Handle OFFSET before LIMIT (some dialects)
        sql = re.sub(r'\bOFFSET\s+(\d+)\s+FETCH\s+NEXT\s+(\d+)\b', r'LIMIT \1, \2', sql, flags=re.IGNORECASE)
        
        # Replace TOP (SQL Server) -> LIMIT
        top_match = re.search(r'\bTOP\s+(\d+)\b', sql, re.IGNORECASE)
        if top_match:
            top_num = top_match.group(1)
            sql = re.sub(r'\bTOP\s+\d+\b', f'LIMIT {top_num}', sql, flags=re.IGNORECASE)
        
        # Replace ROWNUM (Oracle) - complex, needs WHERE clause handling
        # This is approximate - proper handling needs query restructuring
        
        # Replace function calls
        for old_func, new_func in self.function_mappings.items():
            # Skip if new_func is a pattern, not a simple replacement
            if '...' in str(new_func) or '(' in new_func or new_func in ['||', '%']:
                continue
            sql = re.sub(rf'\b{old_func}\s*\(', f'{new_func}(', sql, flags=re.IGNORECASE)
        
        # Handle CONCAT function with multiple arguments (convert to ||)
        sql = re.sub(r'\bCONCAT\s*\(', '(', sql, flags=re.IGNORECASE)
        
        # Handle string concatenation operator variations
        # MySQL uses CONCAT(), PostgreSQL/SQLite use ||
        # Oracle uses || or CONCAT()
        # SQL Server uses +
        
        # Replace SQL Server string concatenation (+)
        # This is tricky - only replace when between string literals or columns
        # For now, we'll do a simple replacement (user may need to adjust)
        
        # Replace data types in function parameters and column definitions
        for old_type, new_type in self.data_type_mappings.items():
            # Match data type with optional size (e.g., VARCHAR(255))
            sql = re.sub(rf'\b{old_type}\s*\([^)]*\)', new_type, sql, flags=re.IGNORECASE)
            # Also match without parentheses for some types
            sql = re.sub(rf'\b{old_type}\b(?![(])', new_type, sql, flags=re.IGNORECASE)
        
        # Replace boolean true/false with SQLite-compatible 1/0
        # Use word boundaries to avoid replacing in strings/names
        sql = re.sub(r'\btrue\b', '1', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bfalse\b', '0', sql, flags=re.IGNORECASE)
        sql = re.sub(r"\b'TRUE'\b", "'1'", sql, flags=re.IGNORECASE)
        sql = re.sub(r"\b'FALSE'\b", "'0'", sql, flags=re.IGNORECASE)
        
        # Replace schema/namespace prefixes (public., dbo., etc.)
        sql = re.sub(r'\bpublic\.(\w+)', r'\1', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bdbo\.(\w+)', r'\1', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bsys\.(\w+)', r'\1', sql, flags=re.IGNORECASE)
        
        # Handle IF EXISTS / IF NOT EXISTS variations
        sql = re.sub(r'\bIF\s+NOT\s+EXISTS\b', 'IF NOT EXISTS', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bIF\s+EXISTS\b', 'IF EXISTS', sql, flags=re.IGNORECASE)
        
        # Handle MERGE/UPSERT statements (convert to INSERT OR REPLACE)
        if re.search(r'\bMERGE\s+INTO\b', sql, re.IGNORECASE):
            sql = self._compile_merge(sql)
        
        # Handle WITH CTEs (Common Table Expressions) - SQLite supports these
        # No transformation needed, but we ensure proper formatting
        
        # Handle window functions hints - SQLite supports basic window functions
        # Remove unsupported hints but keep functions
        
        # Replace double quote identifiers with square brackets (SQL Server -> standard)
        # Actually, SQLite supports both, so we can leave them
        
        # Handle string literals - normalize single vs double quotes if needed
        # SQLite supports both, but we'll prefer single quotes for SQL compatibility
        
        # Replace != with <> (both are valid, but <> is more standard)
        sql = re.sub(r'!=', '<>', sql)
        
        # Handle INNER JOIN explicit keyword (some dialects require it)
        # SQLite supports both JOIN and INNER JOIN
        
        # Handle OUTER JOIN variations
        sql = re.sub(r'\bFULL\s+OUTER\s+JOIN\b', 'LEFT OUTER JOIN', sql, flags=re.IGNORECASE)
        # Note: SQLite doesn't support FULL OUTER JOIN natively
        
        # Handle NVL/NVL2 (Oracle) -> COALESCE
        sql = re.sub(r'\bNVL\s*\(', 'COALESCE(', sql, flags=re.IGNORECASE)
        
        # Handle ISNULL (SQL Server) -> COALESCE
        sql = re.sub(r'\bISNULL\s*\(', 'COALESCE(', sql, flags=re.IGNORECASE)
        
        # Handle LEN (SQL Server) -> LENGTH
        sql = re.sub(r'\bLEN\s*\(', 'LENGTH(', sql, flags=re.IGNORECASE)
        
        # Handle GETDATE() -> datetime('now')
        sql = re.sub(r'\bGETDATE\s*\(\s*\)', "datetime('now')", sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bGETUTCDATE\s*\(\s*\)', "datetime('now', 'utc')", sql, flags=re.IGNORECASE)
        
        # Handle SYSDATE (Oracle) -> datetime('now')
        sql = re.sub(r'\bSYSDATE\s*\(\s*\)', "datetime('now')", sql, flags=re.IGNORECASE)
        
        # Handle RAND() -> RANDOM()
        sql = re.sub(r'\bRAND\s*\(\s*\)', 'RANDOM()', sql, flags=re.IGNORECASE)
        
        return sql
    
    def _compile_merge(self, sql: str) -> str:
        """Compile MERGE/UPSERT statement to INSERT OR REPLACE (SQLite equivalent)."""
        import re
        
        # Extract table name
        table_match = re.search(r'MERGE\s+INTO\s+(\w+)', sql, re.IGNORECASE)
        if not table_match:
            return sql
        
        table_name = table_match.group(1)
        
        # Extract USING/SOURCE table
        using_match = re.search(r'USING\s+(\w+)', sql, re.IGNORECASE)
        source_table = using_match.group(1) if using_match else table_name
        
        # Extract ON condition
        on_match = re.search(r'ON\s+\(([^)]+)\)', sql, re.IGNORECASE | re.DOTALL)
        on_condition = on_match.group(1).strip() if on_match else '1=1'
        
        # Extract WHEN MATCHED clause
        matched_match = re.search(r'WHEN\s+MATCHED\s+THEN\s+UPDATE\s+SET\s+([^W]+)', sql, re.IGNORECASE | re.DOTALL)
        update_clause = matched_match.group(1).strip() if matched_match else ''
        
        # Extract WHEN NOT MATCHED clause (INSERT)
        not_matched_match = re.search(r'WHEN\s+NOT\s+MATCHED\s+THEN\s+INSERT\s+[^(]*\(([^)]+)\)\s+VALUES\s*\(([^)]+)\)', sql, re.IGNORECASE | re.DOTALL)
        
        # For simplicity, convert to INSERT OR REPLACE
        # This is an approximation - full MERGE support is complex
        if not_matched_match:
            columns = not_matched_match.group(1).strip()
            values = not_matched_match.group(2).strip()
            return f"INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({values})"
        
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