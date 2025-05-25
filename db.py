import sqlite3

DB_NAME = "utm.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS drones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        model TEXT,
        serial TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS pilots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        contacts TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS flights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        drone_id INTEGER,
        pilot_id INTEGER,
        route TEXT,
        status TEXT
    )''')
    conn.commit()
    conn.close()

def add_drone_to_db(name, model, serial):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO drones (name, model, serial) VALUES (?, ?, ?)', (name, model, serial))
    conn.commit()
    conn.close()

def add_pilot_to_db(name, contacts):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO pilots (name, contacts) VALUES (?, ?)', (name, contacts))
    conn.commit()
    conn.close()

def get_all_drones():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, name FROM drones')
    drones = c.fetchall()
    conn.close()
    return drones

def get_all_pilots():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, name FROM pilots')
    pilots = c.fetchall()
    conn.close()
    return pilots

def add_flight_to_db(drone_id, pilot_id, route, status="ожидание"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO flights (drone_id, pilot_id, route, status) VALUES (?, ?, ?, ?)',
              (drone_id, pilot_id, route, status))
    conn.commit()
    conn.close()
