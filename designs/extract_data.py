import sqlite3, json, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('master_data_v2.db')
c = conn.cursor()
tables = ['projects','machines','machine_capabilities','machine_speeds','process_definitions','materials']
data = {}
for t in tables:
    rows = c.execute(f'SELECT * FROM {t}').fetchall()
    cols = [d[0] for d in c.description]
    data[t] = [dict(zip(cols, r)) for r in rows]
with open('designs/db_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("OK")
conn.close()
