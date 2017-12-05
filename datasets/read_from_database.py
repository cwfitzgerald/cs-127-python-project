import sys
import json
import sqlite3
import pprint

conn = sqlite3.connect("datasets.sql")

cursor = conn.execute(sys.argv[1])

results = cursor.fetchall()

if results:
    for r in results:
        pprint.pprint([str(x).replace("\\n", "\n") for x in json.loads(r[2])])
else:
    print("None found.")
