import os
print(os.getcwd())
import sqlite3

con = sqlite3.connect('pokebum.db')
cur = con.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, packsAmount INTEGER DEFAULT 0, lastPack TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS pokemons (id INTEGER PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL, card TEXT NOT NULL)')
cur.execute('CREATE TABLE IF NOT EXISTS backgrounds (type TEXT PRIMARY KEY, url TEXT NOT NULL)')
cur.execute('CREATE TABLE IF NOT EXISTS cardsFound (id INTEGER PRIMARY KEY AUTOINCREMENT, pokemonId INTEGER, userId INTEGER)')

con.commit()
con.close()
print('Tablas creadas!')