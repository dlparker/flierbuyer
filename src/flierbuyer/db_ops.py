import sqlite3
import json
from datetime import date
from fuzzywuzzy import fuzz

def setup_db():
    conn = sqlite3.connect('corsair_market.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS listings (
            boat_id TEXT PRIMARY KEY,
            url TEXT UNIQUE,
            model TEXT,
            year INTEGER,
            location TEXT,
            price REAL,
            trailer BOOLEAN,
            has_head BOOLEAN,
            extended_tongue BOOLEAN,
            features TEXT,	-- JSON string
            notes TEXT,
            first_seen DATE,
            last_updated DATE,
            source_site TEXT,
            status TEXT DEFAULT 'Active'
        )
    ''')
    conn.commit()
    conn.close()


def add_or_update(conn, new_entry):
    c = conn.cursor()
    c.execute("SELECT * FROM listings WHERE url = ?", (new_entry['url'],))
    existing = c.fetchone()
    if existing:
        # Update price, features merge
        new_features = json.loads(existing[9])  # features col
        new_features.update(json.loads(new_entry['features']))
        c.execute("UPDATE listings SET price=?, features=?, last_updated=? WHERE url=?",
                  (new_entry['price'], json.dumps(new_features), date.today(), new_entry['url']))
        print(f"Updated {new_entry['url']}: Price now ${new_entry['price']}")
    else:
        # Insert new
        c.execute("INSERT INTO listings VALUES (?,?,?,?,?,?,?,?,?,?,?, ?,?,?)", 
                  (new_entry['boat_id'], new_entry['url'], ...))  # Map fields
        print(f"New: {new_entry['model']} {new_entry['year']} in {new_entry['location']}")
    conn.commit()
    
