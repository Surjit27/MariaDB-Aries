#!/usr/bin/env python3
"""
Test script to demonstrate advanced SQL features support.
"""

from sql_engine.simple_sql_compiler import SimpleSQLCompiler

def test_advanced_sql_features():
    compiler = SimpleSQLCompiler()
    
    print("=== ADVANCED SQL FEATURES SUPPORT ===\n")
    
    # Test 1: Tables with Foreign Keys
    print("1. CREATE TABLE with Foreign Keys:")
    create_with_fk = """
    CREATE TABLE departments (
        dept_id INTEGER PRIMARY KEY,
        dept_name VARCHAR(50) NOT NULL
    );
    
    CREATE TABLE employees (
        emp_id INTEGER PRIMARY KEY,
        first_name VARCHAR(50),
        last_name VARCHAR(50),
        dept_id INTEGER,
        salary DECIMAL(10,2),
        hire_date DATE,
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
    );
    """
    
    for sql in create_with_fk.split(';'):
        if sql.strip():
            compiled = compiler.compile_sql(sql.strip())
            print(f"Original: {sql.strip()}")
            print(f"Compiled: {compiled}")
            print()
    
    # Test 2: JOIN Queries
    print("2. JOIN Queries:")
    join_queries = [
        "SELECT e.first_name, e.last_name, d.dept_name FROM employees e INNER JOIN departments d ON e.dept_id = d.dept_id;",
        "SELECT e.first_name, e.last_name, d.dept_name FROM employees e LEFT OUTER JOIN departments d ON e.dept_id = d.dept_id;",
        "SELECT e.first_name, e.last_name, d.dept_name FROM employees e RIGHT OUTER JOIN departments d ON e.dept_id = d.dept_id;"
    ]
    
    for query in join_queries:
        compiled = compiler.compile_sql(query)
        print(f"Original: {query}")
        print(f"Compiled: {compiled}")
        print()
    
    # Test 3: Complex SELECT with Functions
    print("3. Complex SELECT with Functions:")
    complex_select = """
    SELECT 
        e.first_name,
        e.last_name,
        d.dept_name,
        e.salary,
        NOW() as current_time,
        CURRENT_DATE as today
    FROM employees e
    LEFT JOIN departments d ON e.dept_id = d.dept_id
    WHERE e.salary > 50000
    ORDER BY e.salary DESC;
    """
    
    compiled = compiler.compile_sql(complex_select)
    print(f"Original: {complex_select}")
    print(f"Compiled: {compiled}")
    print()
    
    # Test 4: ALTER TABLE
    print("4. ALTER TABLE:")
    alter_table = "ALTER TABLE employees ADD COLUMN phone VARCHAR(20);"
    compiled = compiler.compile_sql(alter_table)
    print(f"Original: {alter_table}")
    print(f"Compiled: {compiled}")
    print()
    
    # Test 5: CREATE INDEX
    print("5. CREATE INDEX:")
    create_index = "CREATE INDEX idx_employee_name ON employees(first_name, last_name);"
    compiled = compiler.compile_sql(create_index)
    print(f"Original: {create_index}")
    print(f"Compiled: {compiled}")
    print()
    
    # Test 6: UPDATE and DELETE
    print("6. UPDATE and DELETE:")
    update_delete = [
        "UPDATE employees SET salary = salary * 1.1 WHERE dept_id = 1;",
        "DELETE FROM employees WHERE hire_date < '2020-01-01';"
    ]
    
    for query in update_delete:
        compiled = compiler.compile_sql(query)
        print(f"Original: {query}")
        print(f"Compiled: {compiled}")
        print()
    
    # Show supported features
    print("=== SUPPORTED FEATURES ===")
    print("Supported JOINs:", compiler.get_supported_joins())
    print("Supported Constraints:", compiler.get_supported_constraints())
    print("Supported Types:", list(compiler.type_mappings.keys()))

if __name__ == "__main__":
    test_advanced_sql_features()
