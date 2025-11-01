"""
Create a Pokemon World database with extensive sample data
This script creates tables and populates them with a large amount of Pokemon data
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

# Database path
DB_PATH = os.path.join("databases", "pokemon_world.db")

def create_database():
    """Create the Pokemon World database with all tables and extensive sample data."""
    
    # Remove existing database if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Removed existing database")
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    print("Creating Pokemon World database with extensive data...")
    
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
    
    # Insert extensive sample data
    print("Inserting extensive sample data...")
    
    # Regions (8 regions)
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
    
    # Types (18 types)
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
    
    # Abilities (30 abilities)
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
        ('Multiscale', 'Reduces damage when HP is full'),
        ('Shadow Tag', 'Prevents opponent from fleeing'),
        ('Arena Trap', 'Prevents opponent from fleeing'),
        ('Sand Stream', 'Summons a sandstorm'),
        ('Drizzle', 'Summons rain'),
        ('Drought', 'Summons harsh sunlight'),
        ('Snow Warning', 'Summons a hailstorm'),
        ('Pressure', 'Raises opponents PP usage'),
        ('Rough Skin', 'Damages attacker on contact'),
        ('Poison Point', 'May poison attacker on contact'),
        ('Flame Body', 'May burn attacker on contact'),
        ('Cute Charm', 'May cause infatuation on contact'),
        ('Pickup', 'Picks up items after battle'),
        ('Swift Swim', 'Doubles Speed in rain'),
        ('Chlorophyll', 'Doubles Speed in harsh sunlight'),
    ]
    cursor.executemany("INSERT INTO ability (ability_name, description) VALUES (?, ?)", abilities)
    ability_ids = [i+1 for i in range(len(abilities))]
    
    # Pokemon (150+ Pokemon across all generations)
    pokemon_data = []
    
    # Generation 1 Pokemon (Kanto)
    gen1 = [
        ('Bulbasaur', 1, 64, 0.7, 6.9, 45), ('Ivysaur', 1, 142, 1.0, 13.0, 45), ('Venusaur', 1, 236, 2.0, 100.0, 45),
        ('Charmander', 1, 62, 0.6, 8.5, 45), ('Charmeleon', 1, 142, 1.1, 19.0, 45), ('Charizard', 1, 240, 1.7, 90.5, 45),
        ('Squirtle', 1, 63, 0.5, 9.0, 45), ('Wartortle', 1, 142, 1.0, 22.5, 45), ('Blastoise', 1, 239, 1.6, 85.5, 45),
        ('Caterpie', 1, 39, 0.3, 2.9, 255), ('Metapod', 1, 72, 0.7, 9.9, 120), ('Butterfree', 1, 178, 1.1, 32.0, 45),
        ('Weedle', 1, 39, 0.3, 3.2, 255), ('Kakuna', 1, 72, 0.6, 10.0, 120), ('Beedrill', 1, 178, 1.0, 29.5, 45),
        ('Pidgey', 1, 50, 0.3, 1.8, 255), ('Pidgeotto', 1, 122, 1.1, 30.0, 120), ('Pidgeot', 1, 216, 1.5, 39.5, 45),
        ('Rattata', 1, 51, 0.3, 3.5, 255), ('Raticate', 1, 145, 0.7, 18.5, 127),
        ('Spearow', 1, 52, 0.3, 2.0, 255), ('Fearow', 1, 155, 1.2, 38.0, 90),
        ('Ekans', 1, 58, 2.0, 6.9, 255), ('Arbok', 1, 153, 3.5, 65.0, 90),
        ('Pikachu', 1, 112, 0.4, 6.0, 190), ('Raichu', 1, 218, 0.8, 30.0, 75),
        ('Sandshrew', 1, 60, 0.6, 12.0, 255), ('Sandslash', 1, 158, 1.0, 29.5, 90),
        ('Nidoran-F', 1, 55, 0.4, 7.0, 235), ('Nidorina', 1, 128, 0.8, 20.0, 120), ('Nidoqueen', 1, 227, 1.3, 60.0, 45),
        ('Nidoran-M', 1, 55, 0.5, 9.0, 235), ('Nidorino', 1, 128, 0.9, 19.5, 120), ('Nidoking', 1, 227, 1.4, 62.0, 45),
        ('Clefairy', 1, 113, 0.6, 7.5, 150), ('Clefable', 1, 217, 1.3, 40.0, 25),
        ('Vulpix', 1, 60, 0.6, 9.9, 190), ('Ninetales', 1, 177, 1.1, 19.9, 75),
        ('Jigglypuff', 1, 95, 0.5, 5.5, 170), ('Wigglytuff', 1, 196, 1.0, 12.0, 50),
        ('Zubat', 1, 49, 0.8, 7.5, 255), ('Golbat', 1, 159, 1.6, 55.0, 90),
        ('Oddish', 1, 64, 0.5, 5.4, 255), ('Gloom', 1, 138, 0.8, 8.6, 120), ('Vileplume', 1, 221, 1.2, 18.6, 45),
        ('Paras', 1, 57, 0.3, 5.4, 190), ('Parasect', 1, 142, 1.0, 29.5, 75),
        ('Venonat', 1, 61, 1.0, 30.0, 190), ('Venomoth', 1, 158, 1.5, 12.5, 75),
        ('Diglett', 1, 53, 0.2, 0.8, 255), ('Dugtrio', 1, 149, 0.7, 33.3, 50),
        ('Meowth', 1, 58, 0.4, 4.2, 255), ('Persian', 1, 154, 1.0, 32.0, 90),
        ('Psyduck', 1, 64, 0.8, 19.6, 190), ('Golduck', 1, 175, 1.7, 76.6, 75),
        ('Mankey', 1, 61, 0.5, 28.0, 190), ('Primeape', 1, 159, 1.0, 32.0, 75),
        ('Growlithe', 1, 70, 0.7, 19.0, 190), ('Arcanine', 1, 194, 1.9, 155.0, 75),
        ('Poliwag', 1, 60, 0.6, 12.4, 255), ('Poliwhirl', 1, 135, 1.0, 20.0, 120), ('Poliwrath', 1, 230, 1.3, 54.0, 45),
        ('Abra', 1, 62, 0.9, 19.5, 200), ('Kadabra', 1, 140, 1.3, 56.5, 100), ('Alakazam', 1, 225, 1.5, 48.0, 50),
        ('Machop', 1, 61, 0.8, 19.5, 180), ('Machoke', 1, 142, 1.5, 70.5, 90), ('Machamp', 1, 227, 1.6, 130.0, 45),
        ('Bellsprout', 1, 60, 0.7, 4.0, 255), ('Weepinbell', 1, 137, 1.0, 6.4, 120), ('Victreebel', 1, 221, 1.7, 15.5, 45),
        ('Tentacool', 1, 67, 0.9, 45.5, 190), ('Tentacruel', 1, 180, 1.6, 55.0, 60),
        ('Geodude', 1, 60, 0.4, 20.0, 255), ('Graveler', 1, 137, 1.0, 105.0, 120), ('Golem', 1, 223, 1.4, 300.0, 45),
        ('Ponyta', 1, 82, 1.0, 30.0, 190), ('Rapidash', 1, 175, 1.7, 95.0, 60),
        ('Slowpoke', 1, 63, 1.2, 36.0, 190), ('Slowbro', 1, 172, 1.6, 78.5, 75),
        ('Magnemite', 1, 65, 0.3, 6.0, 190), ('Magneton', 1, 163, 1.0, 60.0, 60),
        ('Farfetchd', 1, 132, 0.8, 15.0, 45),
        ('Doduo', 1, 62, 1.4, 39.2, 190), ('Dodrio', 1, 165, 1.8, 85.2, 45),
        ('Seel', 1, 65, 1.1, 90.0, 190), ('Dewgong', 1, 166, 1.7, 120.0, 75),
        ('Grimer', 1, 65, 0.9, 30.0, 190), ('Muk', 1, 175, 1.2, 30.0, 75),
        ('Shellder', 1, 61, 0.3, 4.0, 190), ('Cloyster', 1, 184, 1.5, 132.5, 60),
        ('Gastly', 1, 62, 1.3, 0.1, 190), ('Haunter', 1, 142, 1.6, 0.1, 90), ('Gengar', 1, 225, 1.5, 40.5, 45),
        ('Onix', 1, 77, 8.8, 210.0, 45),
        ('Drowzee', 1, 66, 1.0, 32.4, 190), ('Hypno', 1, 169, 1.6, 75.6, 75),
        ('Krabby', 1, 65, 0.4, 6.5, 225), ('Kingler', 1, 166, 1.3, 60.0, 60),
        ('Voltorb', 1, 66, 0.5, 10.4, 190), ('Electrode', 1, 172, 1.2, 66.6, 60),
        ('Exeggcute', 1, 65, 0.4, 2.5, 90), ('Exeggutor', 1, 186, 2.0, 120.0, 45),
        ('Cubone', 1, 64, 0.4, 6.5, 190), ('Marowak', 1, 149, 1.0, 45.0, 75),
        ('Hitmonlee', 1, 159, 1.5, 49.8, 45), ('Hitmonchan', 1, 159, 1.4, 50.2, 45),
        ('Lickitung', 1, 77, 1.2, 65.5, 45),
        ('Koffing', 1, 68, 0.6, 1.0, 190), ('Weezing', 1, 172, 1.2, 9.5, 60),
        ('Rhyhorn', 1, 69, 1.0, 115.0, 120), ('Rhydon', 1, 170, 1.9, 120.0, 60),
        ('Chansey', 1, 395, 1.1, 34.6, 30),
        ('Tangela', 1, 87, 1.0, 35.0, 45),
        ('Kangaskhan', 1, 172, 2.2, 80.0, 45),
        ('Horsea', 1, 59, 0.4, 8.0, 225), ('Seadra', 1, 154, 1.2, 25.0, 75),
        ('Goldeen', 1, 64, 0.6, 15.0, 225), ('Seaking', 1, 158, 1.3, 39.0, 60),
        ('Staryu', 1, 68, 0.8, 34.5, 225), ('Starmie', 1, 182, 1.1, 80.0, 60),
        ('Mr. Mime', 1, 161, 1.3, 54.5, 45),
        ('Scyther', 1, 100, 1.5, 56.0, 45),
        ('Jynx', 1, 159, 1.4, 40.6, 45),
        ('Electabuzz', 1, 172, 1.1, 30.0, 45),
        ('Magmar', 1, 173, 1.3, 44.5, 45),
        ('Pinsir', 1, 175, 1.5, 55.0, 45),
        ('Tauros', 1, 172, 1.4, 88.4, 45),
        ('Magikarp', 1, 40, 0.9, 10.0, 255), ('Gyarados', 1, 189, 6.5, 235.0, 45),
        ('Lapras', 1, 187, 2.5, 220.0, 45),
        ('Ditto', 1, 101, 0.3, 4.0, 35),
        ('Eevee', 1, 65, 0.3, 6.5, 255),
        ('Vaporeon', 1, 184, 1.0, 29.0, 45), ('Jolteon', 1, 184, 0.8, 24.5, 45), ('Flareon', 1, 184, 0.9, 25.0, 45),
        ('Porygon', 1, 79, 0.8, 36.5, 45),
        ('Omanyte', 1, 71, 0.4, 7.5, 45), ('Omastar', 1, 173, 1.0, 35.0, 45),
        ('Kabuto', 1, 71, 0.5, 11.5, 45), ('Kabutops', 1, 173, 1.3, 40.5, 45),
        ('Aerodactyl', 1, 180, 1.8, 59.0, 45),
        ('Snorlax', 1, 189, 2.1, 460.0, 25),
        ('Articuno', 1, 290, 1.7, 55.4, 3), ('Zapdos', 1, 290, 1.6, 52.6, 3), ('Moltres', 1, 290, 2.0, 60.0, 3),
        ('Dratini', 1, 60, 1.8, 3.3, 45), ('Dragonair', 1, 147, 4.0, 16.5, 45), ('Dragonite', 1, 270, 2.2, 210.0, 45),
        ('Mewtwo', 1, 306, 2.0, 122.0, 3), ('Mew', 1, 300, 0.4, 4.0, 45),
    ]
    pokemon_data.extend(gen1)
    
    # Generation 2 Pokemon (Johto) - Sample
    gen2 = [
        ('Chikorita', 2, 64, 0.9, 6.4, 45), ('Bayleef', 2, 142, 1.2, 15.8, 45), ('Meganium', 2, 236, 1.8, 100.5, 45),
        ('Cyndaquil', 2, 62, 0.5, 7.9, 45), ('Quilava', 2, 142, 0.9, 19.0, 45), ('Typhlosion', 2, 240, 1.7, 79.5, 45),
        ('Totodile', 2, 63, 0.6, 9.5, 45), ('Croconaw', 2, 142, 1.1, 25.0, 45), ('Feraligatr', 2, 239, 2.3, 88.8, 45),
        ('Sentret', 2, 43, 0.8, 6.0, 255), ('Furret', 2, 145, 1.8, 32.5, 90),
        ('Hoothoot', 2, 52, 0.7, 21.2, 255), ('Noctowl', 2, 158, 1.6, 40.8, 90),
        ('Ledyba', 2, 53, 1.0, 10.8, 255), ('Ledian', 2, 137, 1.4, 35.6, 90),
        ('Spinarak', 2, 50, 0.5, 8.5, 255), ('Ariados', 2, 140, 1.1, 33.5, 90),
        ('Crobat', 2, 241, 1.8, 75.0, 90),
        ('Chinchou', 2, 66, 0.5, 12.0, 190), ('Lanturn', 2, 161, 1.2, 22.5, 75),
        ('Pichu', 2, 41, 0.3, 2.0, 190),
        ('Cleffa', 2, 44, 0.3, 3.0, 150),
        ('Igglybuff', 2, 42, 0.3, 1.0, 170),
        ('Togepi', 2, 49, 0.3, 1.5, 190), ('Togetic', 2, 142, 0.6, 3.2, 45),
        ('Natu', 2, 64, 0.2, 2.0, 190), ('Xatu', 2, 165, 1.5, 15.0, 75),
        ('Mareep', 2, 56, 0.6, 7.8, 235), ('Flaaffy', 2, 128, 0.8, 13.3, 120), ('Ampharos', 2, 230, 1.4, 61.5, 45),
        ('Bellossom', 2, 221, 0.4, 5.8, 45),
        ('Marill', 2, 88, 0.4, 8.5, 190), ('Azumarill', 2, 189, 0.8, 28.5, 75),
        ('Sudowoodo', 2, 144, 1.2, 38.0, 65),
        ('Politoed', 2, 250, 1.1, 33.9, 45),
        ('Hoppip', 2, 50, 0.4, 0.5, 255), ('Skiploom', 2, 119, 0.6, 1.0, 120), ('Jumpluff', 2, 207, 0.8, 3.0, 45),
        ('Aipom', 2, 72, 0.8, 11.5, 45),
        ('Sunkern', 2, 36, 0.3, 1.8, 235), ('Sunflora', 2, 149, 0.8, 8.5, 120),
        ('Yanma', 2, 78, 1.2, 38.0, 75),
        ('Wooper', 2, 42, 0.4, 8.5, 255), ('Quagsire', 2, 151, 1.4, 75.0, 90),
        ('Espeon', 2, 184, 0.9, 26.5, 45), ('Umbreon', 2, 184, 1.0, 27.0, 45),
        ('Murkrow', 2, 81, 0.5, 2.1, 30),
        ('Slowking', 2, 172, 2.0, 79.5, 70),
        ('Misdreavus', 2, 87, 0.7, 1.0, 45),
        ('Unown', 2, 118, 0.5, 5.0, 225),
        ('Wobbuffet', 2, 142, 1.3, 28.5, 45),
        ('Girafarig', 2, 159, 1.5, 41.5, 60),
        ('Pineco', 2, 58, 0.6, 7.2, 190), ('Forretress', 2, 163, 1.2, 125.8, 75),
        ('Dunsparce', 2, 145, 1.5, 14.0, 190),
        ('Gligar', 2, 86, 1.1, 64.8, 60),
        ('Steelix', 2, 179, 9.2, 400.0, 25),
        ('Snubbull', 2, 60, 0.6, 7.8, 190), ('Granbull', 2, 158, 1.4, 48.7, 75),
        ('Qwilfish', 2, 88, 0.5, 3.9, 45),
        ('Scizor', 2, 175, 1.8, 118.0, 25),
        ('Shuckle', 2, 177, 0.6, 20.5, 190),
        ('Heracross', 2, 175, 1.5, 54.0, 45),
        ('Sneasel', 2, 86, 0.9, 28.0, 60),
        ('Teddiursa', 2, 66, 0.6, 8.8, 120), ('Ursaring', 2, 175, 1.8, 125.8, 60),
        ('Slugma', 2, 50, 0.7, 35.0, 190), ('Magcargo', 2, 151, 0.8, 55.0, 75),
        ('Swinub', 2, 50, 0.4, 6.5, 225), ('Piloswine', 2, 158, 1.1, 55.8, 75),
        ('Corsola', 2, 144, 0.6, 5.0, 60),
        ('Remoraid', 2, 60, 0.6, 12.0, 190), ('Octillery', 2, 168, 0.9, 28.5, 75),
        ('Delibird', 2, 116, 0.9, 16.0, 45),
        ('Mantine', 2, 170, 2.1, 220.0, 25),
        ('Skarmory', 2, 163, 1.7, 50.5, 25),
        ('Houndour', 2, 66, 0.6, 10.8, 120), ('Houndoom', 2, 175, 1.4, 35.0, 45),
        ('Kingdra', 2, 270, 1.8, 152.0, 45),
        ('Phanpy', 2, 66, 0.5, 33.5, 120), ('Donphan', 2, 175, 1.1, 120.0, 60),
        ('Porygon2', 2, 180, 0.6, 32.5, 45),
        ('Stantler', 2, 163, 1.4, 71.2, 45),
        ('Smeargle', 2, 88, 1.2, 58.0, 45),
        ('Tyrogue', 2, 42, 0.7, 21.0, 75),
        ('Hitmontop', 2, 159, 1.4, 48.0, 45),
        ('Smoochum', 2, 61, 0.4, 6.0, 45),
        ('Elekid', 2, 72, 0.6, 23.5, 45),
        ('Magby', 2, 73, 0.7, 21.4, 45),
        ('Miltank', 2, 172, 1.2, 75.5, 45),
        ('Blissey', 2, 635, 1.5, 46.8, 30),
        ('Raikou', 2, 290, 1.9, 178.0, 3), ('Entei', 2, 290, 2.1, 198.0, 3), ('Suicune', 2, 290, 2.0, 187.0, 3),
        ('Larvitar', 2, 60, 0.6, 72.0, 45), ('Pupitar', 2, 144, 1.2, 152.0, 45), ('Tyranitar', 2, 300, 2.0, 202.0, 45),
        ('Lugia', 2, 306, 5.2, 216.0, 3), ('Ho-Oh', 2, 306, 3.8, 199.0, 3), ('Celebi', 2, 300, 0.6, 5.0, 45),
    ]
    pokemon_data.extend(gen2)
    
    # Insert all Pokemon
    cursor.executemany(
        "INSERT INTO pokemon (name, region_id, base_experience, height, weight, capture_rate) VALUES (?, ?, ?, ?, ?, ?)",
        pokemon_data
    )
    pokemon_ids = [i+1 for i in range(len(pokemon_data))]
    
    print(f"Inserted {len(pokemon_data)} Pokemon")
    
    # Pokemon-Type mappings (assign types based on actual Pokemon)
    pokemon_types = []
    pokemon_types_set = set()  # Track to avoid duplicates
    
    # Define types for each Pokemon (simplified but comprehensive)
    # Format: pokemon_id: [type_id1, type_id2, ...]
    type_assignments = {}
    
    # Gen 1 Pokemon (IDs 1-151)
    gen1_assignments = {
        1: [5, 8],   2: [5, 8],   3: [5, 8],      # Bulbasaur line: Grass/Poison
        4: [2],      5: [2],      6: [2, 10],    # Charmander line: Fire/Flying
        7: [3],      8: [3],      9: [3],        # Squirtle line: Water
        10: [7],     11: [7],     12: [7, 10],   # Caterpie line: Bug/Flying
        13: [7, 8],  14: [7, 8],  15: [7, 8],    # Weedle line: Bug/Poison
        16: [1, 10], 17: [1, 10], 18: [1, 10],   # Pidgey line: Normal/Flying
        19: [1],     20: [1],                    # Rattata line: Normal
        21: [1, 10], 22: [1, 10],                # Spearow line: Normal/Flying
        23: [8],     24: [8],                    # Ekans line: Poison
        25: [4],     26: [4],                    # Pikachu line: Electric
        27: [9],     28: [9],                    # Sandshrew line: Ground
        29: [8],     30: [8],     31: [8, 9],    # Nidoran-F line: Poison/Ground
        32: [8],     33: [8],     34: [8, 9],    # Nidoran-M line: Poison/Ground
        35: [18],    36: [18],                   # Clefairy line: Fairy
        37: [2],     38: [2],                    # Vulpix line: Fire
        39: [1, 18], 40: [1, 18],                # Jigglypuff line: Normal/Fairy
        41: [8, 10], 42: [8, 10],                # Zubat line: Poison/Flying
        43: [5, 8],  44: [5, 8],  45: [5, 8],    # Oddish line: Grass/Poison
        46: [7, 5],  47: [7, 5],                 # Paras line: Bug/Grass
        48: [7, 8],  49: [7, 8],                 # Venonat line: Bug/Poison
        50: [9],     51: [9],                    # Diglett line: Ground
        52: [1],     53: [1],                    # Meowth line: Normal
        54: [3],     55: [3],                    # Psyduck line: Water
        56: [7],     57: [7],                    # Mankey line: Fighting
        58: [2],     59: [2],                    # Growlithe line: Fire
        60: [3],     61: [3],     62: [3, 7],    # Poliwag line: Water/Fighting
        63: [11],    64: [11],    65: [11],      # Abra line: Psychic
        66: [7],     67: [7],     68: [7],       # Machop line: Fighting
        69: [5, 8],  70: [5, 8],  71: [5, 8],    # Bellsprout line: Grass/Poison
        72: [3, 8],  73: [3, 8],                 # Tentacool line: Water/Poison
        74: [6, 9],  75: [6, 9],  76: [6, 9],    # Geodude line: Rock/Ground
        77: [2],     78: [2],                    # Ponyta line: Fire
        79: [3, 11], 80: [3, 11],                # Slowpoke line: Water/Psychic
        81: [4, 17], 82: [4, 17],                # Magnemite line: Electric/Steel
        83: [1, 10],                             # Farfetchd: Normal/Flying
        84: [1, 10], 85: [1, 10],                # Doduo line: Normal/Flying
        86: [3],                                 # Seel: Water
        87: [3, 15],                             # Dewgong: Water/Ice
        88: [8],     89: [8],                    # Grimer line: Poison
        90: [3],     91: [3, 15],                # Shellder line: Water/Ice
        92: [14, 8], 93: [14, 8], 94: [14, 8],   # Gastly line: Ghost/Poison
        95: [6, 9],                              # Onix: Rock/Ground
        96: [11],    97: [11],                   # Drowzee line: Psychic
        98: [3],     99: [3],                    # Krabby line: Water
        100: [4],    101: [4],                   # Voltorb line: Electric
        102: [5, 11], 103: [5, 11],              # Exeggcute line: Grass/Psychic
        104: [9],    105: [9],                   # Cubone line: Ground
        106: [7],    107: [7],                   # Hitmonlee/Hitmonchan: Fighting
        108: [1],                                # Lickitung: Normal
        109: [8],    110: [8],                   # Koffing line: Poison
        111: [9, 6], 112: [9, 6],                # Rhyhorn line: Ground/Rock
        113: [1],                                # Chansey: Normal
        114: [5],                                # Tangela: Grass
        115: [1],                                # Kangaskhan: Normal
        116: [3],    117: [3],                   # Horsea line: Water
        118: [3],    119: [3],                   # Goldeen line: Water
        120: [3],    121: [3, 11],               # Staryu line: Water/Psychic
        122: [11, 18],                           # Mr. Mime: Psychic/Fairy
        123: [7, 10],                            # Scyther: Bug/Flying
        124: [15, 11],                           # Jynx: Ice/Psychic
        125: [4],                                # Electabuzz: Electric
        126: [2],                                # Magmar: Fire
        127: [7],                                # Pinsir: Bug
        128: [1],                                # Tauros: Normal
        129: [3],    130: [3, 10],               # Magikarp line: Water/Flying
        131: [3, 15],                            # Lapras: Water/Ice
        132: [1],                                # Ditto: Normal
        133: [1],                                # Eevee: Normal
        134: [3],                                # Vaporeon: Water
        135: [4],                                # Jolteon: Electric
        136: [2],                                # Flareon: Fire
        137: [1],                                # Porygon: Normal
        138: [6, 3], 139: [6, 3],                # Omanyte line: Rock/Water
        140: [6, 3], 141: [6, 3],                # Kabuto line: Rock/Water
        142: [6, 10],                            # Aerodactyl: Rock/Flying
        143: [1],                                # Snorlax: Normal
        144: [15, 10],                           # Articuno: Ice/Flying
        145: [4, 10],                            # Zapdos: Electric/Flying
        146: [2, 10],                            # Moltres: Fire/Flying
        147: [16],   148: [16],   149: [16, 10], # Dratini line: Dragon/Flying
        150: [11],                               # Mewtwo: Psychic
        151: [11],                               # Mew: Psychic
    }
    type_assignments.update(gen1_assignments)
    
    # Gen 2 Pokemon (IDs 152-251) - Simplified assignments
    for pokemon_id in range(152, min(252, len(pokemon_ids) + 1)):
        if pokemon_id not in type_assignments:
            # Assign random types for remaining Pokemon
            num_types = random.choice([1, 1, 1, 2])  # Mostly single type, sometimes dual
            assigned_types = random.sample(type_ids, num_types)
            type_assignments[pokemon_id] = assigned_types
    
    # Build pokemon_types list from assignments (avoid duplicates)
    for pokemon_idx, type_list in type_assignments.items():
        if pokemon_idx <= len(pokemon_ids):
            for type_id in type_list:
                pair = (pokemon_idx, type_id)
                if pair not in pokemon_types_set:
                    pokemon_types.append(pair)
                    pokemon_types_set.add(pair)
    
    cursor.executemany("INSERT INTO pokemon_type (pokemon_id, type_id) VALUES (?, ?)", pokemon_types)
    print(f"Inserted {len(pokemon_types)} Pokemon-Type relationships")
    
    # Pokemon-Ability mappings (each Pokemon gets 1-2 random abilities)
    pokemon_abilities = []
    for pokemon_id in pokemon_ids:
        num_abilities = random.randint(1, 2)
        selected_abilities = random.sample(ability_ids, min(num_abilities, len(ability_ids)))
        for ability_id in selected_abilities:
            pokemon_abilities.append((pokemon_id, ability_id))
    cursor.executemany("INSERT INTO pokemon_ability (pokemon_id, ability_id) VALUES (?, ?)", pokemon_abilities)
    print(f"Inserted {len(pokemon_abilities)} Pokemon-Ability relationships")
    
    # Trainers (50 trainers)
    trainers = []
    first_names = ['Ash', 'Misty', 'Brock', 'Gary', 'Serena', 'Dawn', 'May', 'Iris', 'Clemont', 'Lillie', 'Gloria', 'Victor', 'Red', 'Blue', 'Ethan', 'Lyra', 'Brendan', 'Lucas', 'Hilbert', 'Hilda', 'Nate', 'Rosa', 'Calem', 'Selene', 'Elio', 'Gladion', 'Hau', 'Chase', 'Elaine', 'Trace', 'Leon', 'Sonia', 'Hop', 'Marnie', 'Bede', 'Klara', 'Avery', 'Mustard', 'Peony', 'Oleana', 'Rose', 'Piers', 'Raihan', 'Nessa', 'Bea', 'Allister', 'Gordie', 'Melony', 'Opal', 'Kabu']
    last_names = ['Ketchum', 'Oak', 'Harrison', 'Watson', 'Stone', 'Birch', 'Rowan', 'Juniper', 'Sycamore', 'Kukui', 'Magnolia', 'Rose', 'Turo', 'Sada']
    hometowns = ['Pallet Town', 'Cerulean City', 'Pewter City', 'Vermilion City', 'Lavender Town', 'Celadon City', 'Fuchsia City', 'Saffron City', 'Cinnabar Island', 'Viridian City', 'New Bark Town', 'Violet City', 'Azalea Town', 'Goldenrod City', 'Ecruteak City', 'Olivine City', 'Mahogany Town', 'Blackthorn City', 'Littleroot Town', 'Oldale Town', 'Petalburg City', 'Rustboro City', 'Dewford Town', 'Mauville City', 'Verdanturf Town', 'Fallarbor Town', 'Lavaridge Town', 'Twinleaf Town', 'Sandgem Town', 'Jubilife City', 'Oreburgh City', 'Floaroma Town', 'Nuvema Town', 'Accumula Town', 'Striaton City', 'Nacrene City', 'Castelia City', 'Nimbasa City', 'Vaniville Town', 'Aquacorde Town', 'Santalune City', 'Lumiose City', 'Camphrier Town', 'Hauoli City', 'Iki Town', 'Heahea City', 'Paniola Town', 'Konikoni City', 'Malie City', 'Postwick']
    genders = ['Male', 'Female', 'Other']
    
    for i in range(50):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names) if random.random() > 0.3 else ''
        trainer_name = f"{first_name} {last_name}".strip()
        gender = random.choice(genders)
        hometown = random.choice(hometowns)
        region_id = random.choice(region_ids)
        trainers.append((trainer_name, gender, hometown, region_id))
    
    cursor.executemany(
        "INSERT INTO trainer (trainer_name, gender, hometown, region_id) VALUES (?, ?, ?, ?)",
        trainers
    )
    trainer_ids = [i+1 for i in range(len(trainers))]
    print(f"Inserted {len(trainers)} trainers")
    
    # Pokemon-Trainer mappings (each trainer has 3-8 Pokemon)
    pokemon_trainers = []
    base_date = datetime(2020, 1, 1)
    for trainer_id in trainer_ids:
        num_pokemon = random.randint(3, 8)
        selected_pokemon = random.sample(pokemon_ids, min(num_pokemon, len(pokemon_ids)))
        for i, pokemon_id in enumerate(selected_pokemon):
            caught_date = (base_date + timedelta(days=random.randint(0, 730))).strftime('%Y-%m-%d')
            level = random.randint(5, 100)
            nickname = None if random.random() > 0.3 else f"{random.choice(['Buddy', 'Sparky', 'Fluffy', 'Rex', 'Zap', 'Blaze', 'Shadow', 'Storm', 'Thunder', 'Ice'])}{i+1}"
            pokemon_trainers.append((trainer_id, pokemon_id, nickname, level, caught_date))
    
    cursor.executemany(
        "INSERT INTO pokemon_trainer (trainer_id, pokemon_id, nickname, level, caught_date) VALUES (?, ?, ?, ?, ?)",
        pokemon_trainers
    )
    print(f"Inserted {len(pokemon_trainers)} Pokemon-Trainer relationships")
    
    # Battles (100 battles)
    battles = []
    battle_locations = ['Indigo Plateau', 'Battle Tower', 'Elite Four', 'Gym', 'Route 1', 'Route 22', 'Cerulean Gym', 'Vermilion Gym', 'Lavender Gym', 'Celadon Gym', 'Fuchsia Gym', 'Saffron Gym', 'Cinnabar Gym', 'Viridian Gym', 'Pokemon League', 'Victory Road', 'Cerulean Cave', 'Mt. Moon', 'Diglett Cave', 'Rock Tunnel']
    for i in range(100):
        battle_date = (base_date + timedelta(days=random.randint(50, 900))).strftime('%Y-%m-%d')
        location = random.choice(battle_locations)
        winner = random.choice(trainer_ids)
        battles.append((location, battle_date, winner))
    cursor.executemany(
        "INSERT INTO battle (location, battle_date, winner_trainer_id) VALUES (?, ?, ?)",
        battles
    )
    battle_ids = [i+1 for i in range(len(battles))]
    print(f"Inserted {len(battles)} battles")
    
    # Battle-Pokemon mappings (each battle has 2-6 Pokemon)
    battle_pokemons = []
    for battle_id in battle_ids:
        num_pokemon = random.randint(2, 6)
        selected_trainers = random.sample(trainer_ids, min(2, len(trainer_ids)))
        winner_id = battles[battle_id-1][2]  # Get winner from battle
        
        battle_pokemon_set = set()
        for trainer_id in selected_trainers:
            # Get trainer's Pokemon
            trainer_pokemon = [pt[1] for pt in pokemon_trainers if pt[0] == trainer_id]
            if trainer_pokemon:
                num_trainer_pokemon = random.randint(1, min(3, len(trainer_pokemon)))
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
    print(f"Inserted {len(battle_pokemons)} Battle-Pokemon entries")
    
    conn.commit()
    conn.close()
    
    print(f"\n[SUCCESS] Pokemon World database created successfully!")
    print(f"   Location: {DB_PATH}")
    print(f"\nDatabase Statistics:")
    print(f"   - Regions: {len(regions)}")
    print(f"   - Types: {len(types)}")
    print(f"   - Abilities: {len(abilities)}")
    print(f"   - Pokemon: {len(pokemon_data)}")
    print(f"   - Pokemon-Type relationships: {len(pokemon_types)}")
    print(f"   - Pokemon-Ability relationships: {len(pokemon_abilities)}")
    print(f"   - Trainers: {len(trainers)}")
    print(f"   - Pokemon-Trainer pairs: {len(pokemon_trainers)}")
    print(f"   - Battles: {len(battles)}")
    print(f"   - Battle-Pokemon entries: {len(battle_pokemons)}")
    print(f"\nTotal records: {len(regions) + len(types) + len(abilities) + len(pokemon_data) + len(pokemon_types) + len(pokemon_abilities) + len(trainers) + len(pokemon_trainers) + len(battles) + len(battle_pokemons)}")

if __name__ == "__main__":
    create_database()