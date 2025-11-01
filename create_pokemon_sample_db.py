"""
Create a Pokemon World database with sample data
This script creates tables and populates them with Pokemon data
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

# Database path
DB_PATH = os.path.join("databases", "pokemon_world.db")

def create_database():
    """Create the Pokemon World database with all tables and sample data."""
    
    # Remove existing database if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Removed existing database")
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    print("Creating Pokemon World database...")
    
    # 1. Type Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS type (
            type_id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_name TEXT NOT NULL UNIQUE
        )
    """)
    
    # 2. Region Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS region (
            region_id INTEGER PRIMARY KEY AUTOINCREMENT,
            region_name TEXT NOT NULL UNIQUE
        )
    """)
    
    # 3. Ability Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ability (
            ability_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ability_name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    """)
    
    # 4. Pokémon Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pokemon (
            pokemon_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            region_id INTEGER,
            base_experience INTEGER,
            height REAL,
            weight REAL,
            capture_rate INTEGER,
            FOREIGN KEY (region_id) REFERENCES region(region_id)
        )
    """)
    
    # 5. Pokémon-Type Mapping
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pokemon_type (
            pokemon_id INTEGER,
            type_id INTEGER,
            PRIMARY KEY (pokemon_id, type_id),
            FOREIGN KEY (pokemon_id) REFERENCES pokemon(pokemon_id) ON DELETE CASCADE,
            FOREIGN KEY (type_id) REFERENCES type(type_id) ON DELETE CASCADE
        )
    """)
    
    # 6. Pokémon-Ability Mapping
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pokemon_ability (
            pokemon_id INTEGER,
            ability_id INTEGER,
            PRIMARY KEY (pokemon_id, ability_id),
            FOREIGN KEY (pokemon_id) REFERENCES pokemon(pokemon_id) ON DELETE CASCADE,
            FOREIGN KEY (ability_id) REFERENCES ability(ability_id) ON DELETE CASCADE
        )
    """)
    
    # 7. Trainer Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trainer (
            trainer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            trainer_name TEXT NOT NULL,
            gender TEXT,
            hometown TEXT,
            region_id INTEGER,
            FOREIGN KEY (region_id) REFERENCES region(region_id)
        )
    """)
    
    # 8. Pokémon-Trainer Mapping
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pokemon_trainer (
            trainer_id INTEGER,
            pokemon_id INTEGER,
            nickname TEXT,
            level INTEGER DEFAULT 1,
            caught_date TEXT,
            PRIMARY KEY (trainer_id, pokemon_id),
            FOREIGN KEY (trainer_id) REFERENCES trainer(trainer_id) ON DELETE CASCADE,
            FOREIGN KEY (pokemon_id) REFERENCES pokemon(pokemon_id) ON DELETE CASCADE
        )
    """)
    
    # 9. Battle Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS battle (
            battle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT,
            battle_date TEXT,
            winner_trainer_id INTEGER,
            FOREIGN KEY (winner_trainer_id) REFERENCES trainer(trainer_id)
        )
    """)
    
    # 10. Battle-Pokémon Mapping
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS battle_pokemon (
            battle_id INTEGER,
            pokemon_id INTEGER,
            trainer_id INTEGER,
            is_winner INTEGER DEFAULT 0,
            PRIMARY KEY (battle_id, pokemon_id),
            FOREIGN KEY (battle_id) REFERENCES battle(battle_id) ON DELETE CASCADE,
            FOREIGN KEY (pokemon_id) REFERENCES pokemon(pokemon_id) ON DELETE CASCADE,
            FOREIGN KEY (trainer_id) REFERENCES trainer(trainer_id) ON DELETE CASCADE
        )
    """)
    
    print("Tables created successfully!")
    
    # Insert sample data
    print("Inserting sample data...")
    
    # Regions
    regions = [
        ('Kanto',),
        ('Johto',),
        ('Hoenn',),
        ('Sinnoh',),
        ('Unova',),
        ('Kalos',),
        ('Alola',),
        ('Galar',)
    ]
    cursor.executemany("INSERT INTO region (region_name) VALUES (?)", regions)
    region_ids = [i+1 for i in range(len(regions))]
    
    # Types
    types = [
        ('Normal',),
        ('Fire',),
        ('Water',),
        ('Electric',),
        ('Grass',),
        ('Ice',),
        ('Fighting',),
        ('Poison',),
        ('Ground',),
        ('Flying',),
        ('Psychic',),
        ('Bug',),
        ('Rock',),
        ('Ghost',),
        ('Dragon',),
        ('Dark',),
        ('Steel',),
        ('Fairy',)
    ]
    cursor.executemany("INSERT INTO type (type_name) VALUES (?)", types)
    type_ids = [i+1 for i in range(len(types))]
    
    # Abilities
    abilities = [
        ('Blaze', 'Powers up Fire-type moves when HP is low'),
        ('Torrent', 'Powers up Water-type moves when HP is low'),
        ('Overgrow', 'Powers up Grass-type moves when HP is low'),
        ('Lightning Rod', 'Draws in all Electric-type moves'),
        ('Intimidate', 'Lowers opponents Attack stat'),
        ('Static', 'May cause paralysis when contacted'),
        ('Water Absorb', 'Restores HP if hit by Water-type moves'),
        ('Volt Absorb', 'Restores HP if hit by Electric-type moves'),
        ('Synchronize', 'Passes status conditions to opponent'),
        ('Run Away', 'Can always flee from wild Pokemon'),
        ('Adaptability', 'Powers up moves of the same type'),
        ('Technician', 'Powers up weak moves'),
        ('Moxie', 'Raises Attack after knocking out opponent'),
        ('Huge Power', 'Doubles Attack stat'),
        ('Magic Guard', 'Only takes damage from attacks'),
    ]
    cursor.executemany("INSERT INTO ability (ability_name, description) VALUES (?, ?)", abilities)
    ability_ids = [i+1 for i in range(len(abilities))]
    
    # Pokemon (50 Pokemon)
    pokemon_data = [
        ('Bulbasaur', 1, 64, 0.7, 6.9, 45),
        ('Charmander', 1, 62, 0.6, 8.5, 45),
        ('Squirtle', 1, 63, 0.5, 9.0, 45),
        ('Pikachu', 1, 112, 0.4, 6.0, 190),
        ('Eevee', 1, 65, 0.3, 6.5, 255),
        ('Charmeleon', 1, 142, 1.1, 19.0, 45),
        ('Charizard', 1, 240, 1.7, 90.5, 45),
        ('Wartortle', 1, 142, 1.0, 22.5, 45),
        ('Blastoise', 1, 239, 1.6, 85.5, 45),
        ('Ivysaur', 1, 142, 1.0, 13.0, 45),
        ('Venusaur', 1, 236, 2.0, 100.0, 45),
        ('Raichu', 1, 218, 0.8, 30.0, 75),
        ('Jigglypuff', 1, 95, 0.5, 5.5, 170),
        ('Wigglytuff', 1, 196, 1.0, 12.0, 50),
        ('Meowth', 1, 58, 0.4, 4.2, 255),
        ('Persian', 1, 154, 1.0, 32.0, 90),
        ('Psyduck', 1, 64, 0.8, 19.6, 190),
        ('Golduck', 1, 175, 1.7, 76.6, 75),
        ('Mankey', 1, 61, 0.5, 28.0, 190),
        ('Primeape', 1, 159, 1.0, 32.0, 75),
        ('Growlithe', 1, 70, 0.7, 19.0, 190),
        ('Arcanine', 1, 194, 1.9, 155.0, 75),
        ('Poliwag', 1, 60, 0.6, 12.4, 255),
        ('Poliwhirl', 1, 135, 1.0, 20.0, 120),
        ('Poliwrath', 1, 230, 1.3, 54.0, 45),
        ('Abra', 1, 62, 0.9, 19.5, 200),
        ('Kadabra', 1, 140, 1.3, 56.5, 100),
        ('Alakazam', 1, 225, 1.5, 48.0, 50),
        ('Machop', 1, 61, 0.8, 19.5, 180),
        ('Machoke', 1, 142, 1.5, 70.5, 90),
        ('Machamp', 1, 227, 1.6, 130.0, 45),
        ('Bellsprout', 1, 60, 0.7, 4.0, 255),
        ('Weepinbell', 1, 137, 1.0, 6.4, 120),
        ('Victreebel', 1, 221, 1.7, 15.5, 45),
        ('Tentacool', 1, 67, 0.9, 45.5, 190),
        ('Tentacruel', 1, 180, 1.6, 55.0, 60),
        ('Geodude', 1, 60, 0.4, 20.0, 255),
        ('Graveler', 1, 137, 1.0, 105.0, 120),
        ('Golem', 1, 223, 1.4, 300.0, 45),
        ('Ponyta', 1, 82, 1.0, 30.0, 190),
        ('Rapidash', 1, 175, 1.7, 95.0, 60),
        ('Slowpoke', 1, 63, 1.2, 36.0, 190),
        ('Slowbro', 1, 172, 1.6, 78.5, 75),
        ('Magnemite', 1, 65, 0.3, 6.0, 190),
        ('Magneton', 1, 163, 1.0, 60.0, 60),
        ('Farfetchd', 1, 132, 0.8, 15.0, 45),
        ('Doduo', 1, 62, 1.4, 39.2, 190),
        ('Dodrio', 1, 165, 1.8, 85.2, 45),
        ('Seel', 1, 65, 1.1, 90.0, 190),
        ('Dewgong', 1, 166, 1.7, 120.0, 75),
        ('Grimer', 1, 65, 0.9, 30.0, 190),
        ('Muk', 1, 175, 1.2, 30.0, 75),
    ]
    cursor.executemany(
        "INSERT INTO pokemon (name, region_id, base_experience, height, weight, capture_rate) VALUES (?, ?, ?, ?, ?, ?)",
        pokemon_data
    )
    pokemon_ids = [i+1 for i in range(len(pokemon_data))]
    
    # Pokemon-Type mappings (each Pokemon has 1-2 types)
    pokemon_types = [
        (1, 5), (1, 8),   # Bulbasaur: Grass/Poison
        (2, 2),           # Charmander: Fire
        (3, 3),           # Squirtle: Water
        (4, 4),           # Pikachu: Electric
        (5, 1),           # Eevee: Normal
        (6, 2),           # Charmeleon: Fire
        (7, 2), (7, 10),  # Charizard: Fire/Flying
        (8, 3),           # Wartortle: Water
        (9, 3),           # Blastoise: Water
        (10, 5), (10, 8), # Ivysaur: Grass/Poison
        (11, 5), (11, 8), # Venusaur: Grass/Poison
        (12, 4),          # Raichu: Electric
        (13, 1),          # Jigglypuff: Normal
        (14, 1),          # Wigglytuff: Normal
        (15, 1),          # Meowth: Normal
        (16, 1),          # Persian: Normal
        (17, 3),          # Psyduck: Water
        (18, 3),          # Golduck: Water
        (19, 7),          # Mankey: Fighting
        (20, 7),          # Primeape: Fighting
        (21, 2),          # Growlithe: Fire
        (22, 2),          # Arcanine: Fire
        (23, 3),          # Poliwag: Water
        (24, 3),          # Poliwhirl: Water
        (25, 3), (25, 7), # Poliwrath: Water/Fighting
        (26, 11),         # Abra: Psychic
        (27, 11),         # Kadabra: Psychic
        (28, 11),         # Alakazam: Psychic
        (29, 7),          # Machop: Fighting
        (30, 7),          # Machoke: Fighting
        (31, 7),          # Machamp: Fighting
        (32, 5), (32, 8), # Bellsprout: Grass/Poison
        (33, 5), (33, 8), # Weepinbell: Grass/Poison
        (34, 5), (34, 8), # Victreebel: Grass/Poison
        (35, 3), (35, 8), # Tentacool: Water/Poison
        (36, 3), (36, 8), # Tentacruel: Water/Poison
        (37, 6), (37, 9), # Geodude: Rock/Ground
        (38, 6), (38, 9), # Graveler: Rock/Ground
        (39, 6), (39, 9), # Golem: Rock/Ground
        (40, 2),          # Ponyta: Fire
        (41, 2),          # Rapidash: Fire
        (42, 3), (42, 11), # Slowpoke: Water/Psychic
        (43, 3), (43, 11), # Slowbro: Water/Psychic
        (44, 4), (44, 17), # Magnemite: Electric/Steel
        (45, 4), (45, 17), # Magneton: Electric/Steel
        (46, 1), (46, 10), # Farfetchd: Normal/Flying
        (47, 1), (47, 10), # Doduo: Normal/Flying
        (48, 1), (48, 10), # Dodrio: Normal/Flying
        (49, 3),          # Seel: Water
        (50, 3), (50, 6), # Dewgong: Water/Ice
        (51, 8),          # Grimer: Poison
        (52, 8),          # Muk: Poison
    ]
    cursor.executemany("INSERT INTO pokemon_type (pokemon_id, type_id) VALUES (?, ?)", pokemon_types)
    
    # Pokemon-Ability mappings (each Pokemon has 1-2 abilities)
    pokemon_abilities = []
    for pokemon_id in pokemon_ids[:30]:  # Give abilities to first 30 Pokemon
        # Each Pokemon gets 1-2 random abilities
        num_abilities = random.randint(1, 2)
        selected_abilities = random.sample(ability_ids, min(num_abilities, len(ability_ids)))
        for ability_id in selected_abilities:
            pokemon_abilities.append((pokemon_id, ability_id))
    cursor.executemany("INSERT INTO pokemon_ability (pokemon_id, ability_id) VALUES (?, ?)", pokemon_abilities)
    
    # Trainers (20 trainers)
    trainers = [
        ('Ash Ketchum', 'Male', 'Pallet Town', 1),
        ('Misty', 'Female', 'Cerulean City', 1),
        ('Brock', 'Male', 'Pewter City', 1),
        ('Gary Oak', 'Male', 'Pallet Town', 1),
        ('Serena', 'Female', 'Vaniville Town', 6),
        ('Dawn', 'Female', 'Twinleaf Town', 4),
        ('May', 'Female', 'Littleroot Town', 3),
        ('Iris', 'Female', 'Village of Dragons', 5),
        ('Clemont', 'Male', 'Lumiose City', 6),
        ('Lillie', 'Female', 'Hauoli City', 7),
        ('Gloria', 'Female', 'Postwick', 8),
        ('Victor', 'Male', 'Postwick', 8),
        ('Red', 'Male', 'Pallet Town', 1),
        ('Blue', 'Male', 'Pallet Town', 1),
        ('Ethan', 'Male', 'New Bark Town', 2),
        ('Lyra', 'Female', 'New Bark Town', 2),
        ('Brendan', 'Male', 'Littleroot Town', 3),
        ('Lucas', 'Male', 'Twinleaf Town', 4),
        ('Hilbert', 'Male', 'Nuvema Town', 5),
        ('Hilda', 'Female', 'Nuvema Town', 5),
    ]
    cursor.executemany(
        "INSERT INTO trainer (trainer_name, gender, hometown, region_id) VALUES (?, ?, ?, ?)",
        trainers
    )
    trainer_ids = [i+1 for i in range(len(trainers))]
    
    # Pokemon-Trainer mappings (each trainer has 3-6 Pokemon)
    pokemon_trainers = []
    base_date = datetime(2020, 1, 1)
    for trainer_id in trainer_ids:
        num_pokemon = random.randint(3, 6)
        selected_pokemon = random.sample(pokemon_ids, min(num_pokemon, len(pokemon_ids)))
        for i, pokemon_id in enumerate(selected_pokemon):
            caught_date = (base_date + timedelta(days=random.randint(0, 365*2))).strftime('%Y-%m-%d')
            level = random.randint(1, 100)
            nickname = None if random.random() > 0.3 else f"Buddy{i+1}"
            pokemon_trainers.append((trainer_id, pokemon_id, nickname, level, caught_date))
    cursor.executemany(
        "INSERT INTO pokemon_trainer (trainer_id, pokemon_id, nickname, level, caught_date) VALUES (?, ?, ?, ?, ?)",
        pokemon_trainers
    )
    
    # Battles (30 battles)
    battles = []
    battle_locations = ['Indigo Plateau', 'Battle Tower', 'Elite Four', 'Gym', 'Route 1', 'Route 22', 'Cerulean Gym', 'Vermilion Gym']
    for i in range(30):
        battle_date = (base_date + timedelta(days=random.randint(100, 700))).strftime('%Y-%m-%d')
        location = random.choice(battle_locations)
        winner = random.choice(trainer_ids)
        battles.append((location, battle_date, winner))
    cursor.executemany(
        "INSERT INTO battle (location, battle_date, winner_trainer_id) VALUES (?, ?, ?)",
        battles
    )
    battle_ids = [i+1 for i in range(len(battles))]
    
    # Battle-Pokemon mappings (each battle has 2-4 Pokemon)
    battle_pokemons = []
    for battle_id in battle_ids:
        num_pokemon = random.randint(2, 4)
        selected_trainers = random.sample(trainer_ids, min(2, len(trainer_ids)))
        winner_id = battles[battle_id-1][2]  # Get winner from battle
        
        battle_pokemon_set = set()
        for trainer_id in selected_trainers:
            # Get trainer's Pokemon
            trainer_pokemon = [pt[1] for pt in pokemon_trainers if pt[0] == trainer_id]
            if trainer_pokemon:
                num_trainer_pokemon = random.randint(1, min(2, len(trainer_pokemon)))
                selected_pokemon = random.sample(trainer_pokemon, num_trainer_pokemon)
                for pokemon_id in selected_pokemon:
                    if (battle_id, pokemon_id) not in battle_pokemon_set:
                        is_winner = 1 if trainer_id == winner_id else 0
                        battle_pokemons.append((battle_id, pokemon_id, trainer_id, is_winner))
                        battle_pokemon_set.add((battle_id, pokemon_id))
    
    cursor.executemany(
        "INSERT INTO battle_pokemon (battle_id, pokemon_id, trainer_id, is_winner) VALUES (?, ?, ?, ?)",
        battle_pokemons
    )
    
    conn.commit()
    conn.close()
    
    print(f"\n[SUCCESS] Pokemon World database created successfully!")
    print(f"   Location: {DB_PATH}")
    print(f"\nDatabase Statistics:")
    print(f"   - Regions: {len(regions)}")
    print(f"   - Types: {len(types)}")
    print(f"   - Abilities: {len(abilities)}")
    print(f"   - Pokemon: {len(pokemon_data)}")
    print(f"   - Trainers: {len(trainers)}")
    print(f"   - Pokemon-Trainer pairs: {len(pokemon_trainers)}")
    print(f"   - Battles: {len(battles)}")
    print(f"   - Battle-Pokemon entries: {len(battle_pokemons)}")

if __name__ == "__main__":
    create_database()
