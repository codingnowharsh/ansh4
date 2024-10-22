import sqlite3

conn=sqlite3.connect("expenses.db")
cur=conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS expenses
(id INTEGER PRIMARY KEY,
Date DATE,
description TEXT,
CATEGORY text,
price REAL)""")

   