import sqlite3

with open("init_db.sql", "r", encoding="utf-8") as f:
    sql = f.read()

conn = sqlite3.connect("data.sqlite")
conn.executescript(sql)
conn.commit()
conn.close()

print("✅ 資料庫初始化成功！")


