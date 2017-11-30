import sqlite3
import csv
import sys
import pickle

if __name__ == "__main__":
    if (len(sys.argv) != 3):
        print("Usage: {} <input_csv> <id_col>")
        exit(1)

    filename = sys.argv[1]
    id_col = int(sys.argv[2])

    connect = sqlite3.connect("datasets.csv")

    c = connect.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS data (filename text, id text, contents text)''')
    c.execute('''DELETE FROM data WHERE filename = :name''', {"name": filename})

    csv_reader = csv.reader(open(filename, encoding="utf8", errors="ignore"))
    csv_reader.__next__()  # Skip header

    for row in csv_reader:
        id_val = row[id_col]
        c.execute('''INSERT INTO data (filename, id, contents) VALUES (:filename, :id, :contents)''',
                  {"filename": filename, "id": id_val, "contents": pickle.dump(row)})

    c.commit()
