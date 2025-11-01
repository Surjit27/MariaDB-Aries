"""
Test script for Pokemon World schema creation
Tests multi-statement SQL execution
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from db.enhanced_database_manager import EnhancedDatabaseManager
from sql_engine.simple_sql_compiler import SimpleSQLCompiler

# Test SQL (your Pokemon schema)
test_sql = """CREATE DATABASE pokemon_world;
USE pokemon_world;

-- 1️⃣ Type Table
CREATE TABLE type (
    type_id INT AUTO_INCREMENT PRIMARY KEY,
    type_name VARCHAR(50) NOT NULL UNIQUE
);

-- 2️⃣ Region Table
CREATE TABLE region (
    region_id INT AUTO_INCREMENT PRIMARY KEY,
    region_name VARCHAR(50) NOT NULL UNIQUE
);

-- 3️⃣ Ability Table
CREATE TABLE ability (
    ability_id INT AUTO_INCREMENT PRIMARY KEY,
    ability_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

-- 4️⃣ Pokémon Table
CREATE TABLE pokemon (
    pokemon_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    region_id INT,
    base_experience INT,
    height DECIMAL(4,1),
    weight DECIMAL(4,1),
    capture_rate INT,
    FOREIGN KEY (region_id) REFERENCES region(region_id)
);

-- 5️⃣ Pokémon-Type Mapping (many-to-many)
CREATE TABLE pokemon_type (
    pokemon_id INT,
    type_id INT,
    PRIMARY KEY (pokemon_id, type_id),
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(pokemon_id) ON DELETE CASCADE,
    FOREIGN KEY (type_id) REFERENCES type(type_id) ON DELETE CASCADE
);

-- 6️⃣ Pokémon-Ability Mapping (many-to-many)
CREATE TABLE pokemon_ability (
    pokemon_id INT,
    ability_id INT,
    PRIMARY KEY (pokemon_id, ability_id),
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(pokemon_id) ON DELETE CASCADE,
    FOREIGN KEY (ability_id) REFERENCES ability(ability_id) ON DELETE CASCADE
);

-- 7️⃣ Trainer Table
CREATE TABLE trainer (
    trainer_id INT AUTO_INCREMENT PRIMARY KEY,
    trainer_name VARCHAR(100) NOT NULL,
    gender ENUM('Male', 'Female', 'Other'),
    hometown VARCHAR(100),
    region_id INT,
    FOREIGN KEY (region_id) REFERENCES region(region_id)
);

-- 8️⃣ Pokémon-Trainer Mapping (many-to-many)
CREATE TABLE pokemon_trainer (
    trainer_id INT,
    pokemon_id INT,
    nickname VARCHAR(100),
    level INT DEFAULT 1,
    caught_date DATE,
    PRIMARY KEY (trainer_id, pokemon_id),
    FOREIGN KEY (trainer_id) REFERENCES trainer(trainer_id) ON DELETE CASCADE,
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(pokemon_id) ON DELETE CASCADE
);

-- 9️⃣ Battle Table
CREATE TABLE battle (
    battle_id INT AUTO_INCREMENT PRIMARY KEY,
    location VARCHAR(100),
    battle_date DATE,
    winner_trainer_id INT,
    FOREIGN KEY (winner_trainer_id) REFERENCES trainer(trainer_id)
);

-- 🔟 Battle-Pokémon Mapping (Pokémon participating in each battle)
CREATE TABLE battle_pokemon (
    battle_id INT,
    pokemon_id INT,
    trainer_id INT,
    is_winner BOOLEAN,
    PRIMARY KEY (battle_id, pokemon_id),
    FOREIGN KEY (battle_id) REFERENCES battle(battle_id) ON DELETE CASCADE,
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(pokemon_id) ON DELETE CASCADE,
    FOREIGN KEY (trainer_id) REFERENCES trainer(trainer_id) ON DELETE CASCADE
);
"""

def test_schema_creation():
    """Test creating the Pokemon schema."""
    print("=" * 60)
    print("Testing Pokemon World Schema Creation")
    print("=" * 60)
    
    # Initialize database manager
    db_path = os.path.join(project_root, "databases")
    db_manager = EnhancedDatabaseManager(db_path)
    
    # Test compiler
    compiler = SimpleSQLCompiler()
    print("\n1. Testing SQL Compiler...")
    compiled = compiler.compile_sql("CREATE TABLE test (id INT AUTO_INCREMENT PRIMARY KEY);")
    print(f"   Original: CREATE TABLE test (id INT AUTO_INCREMENT PRIMARY KEY);")
    print(f"   Compiled: {compiled}")
    
    # Execute the schema creation
    print("\n2. Executing Pokemon schema SQL...")
    columns, results, error = db_manager.execute_query(test_sql)
    
    if error:
        print(f"\n❌ Error: {error}")
        return False
    
    print(f"\n✅ Success! {error if error else 'All statements executed successfully'}")
    
    # Verify tables were created
    if db_manager.current_db == "pokemon_world":
        print("\n3. Verifying tables...")
        tables = db_manager.get_tables()
        print(f"   Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table}")
        
        # Test inserting data
        print("\n4. Testing data insertion...")
        test_insert = """
        INSERT INTO region (region_name) VALUES ('Kanto');
        INSERT INTO type (type_name) VALUES ('Fire'), ('Water'), ('Grass');
        INSERT INTO ability (ability_name, description) VALUES ('Blaze', 'Boosts Fire moves');
        """
        
        cols, res, err = db_manager.execute_query(test_insert)
        if err:
            print(f"   ⚠️  Insert warning: {err}")
        else:
            print("   ✅ Test data inserted successfully!")
        
        # Query to verify
        print("\n5. Verifying data...")
        verify_query = "SELECT * FROM region;"
        cols, res, err = db_manager.execute_query(verify_query)
        if not err and res:
            print(f"   ✅ Found {len(res)} region(s):")
            for row in res:
                print(f"      {row}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_schema_creation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
