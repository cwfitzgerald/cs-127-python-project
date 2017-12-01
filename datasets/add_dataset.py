import sqlite3
import csv
import sys
import json
import os
import itertools
import operator

# This method takes .csv file names as arguments and checks whether they exist in index.JSON.
# If so, creates a SQL database from the CSV file, with three columns, filename, id, and contents.
# This is in order to deal with the massive data amounts in the CSV's, and not have to
# iterate through everything in order to reach the file contents when displaying the results.

if __name__ == "__main__":
    if (sys.argv[1] in ["--delete", "-d"]):
        delete = True
    else:
        delete = False

    if (len(sys.argv) < 3):
        print("Usage: {} [<input_csv>]*".format(sys.argv[0]))
        exit(1)

    settings = json.load(open("index.json"))

    csv.field_size_limit(2**31 - 1)

    filenames = list(map(os.path.abspath, sys.argv[2 if delete else 1:]))
    filenames_short = list(map(os.path.basename, filenames))

    in_json = [x in settings for x in filenames_short]

    for f, j in zip(filenames, in_json):
        if not j:
            print("{} isn't in .json".format(f))

    filenames = list(itertools.compress(filenames, in_json))
    filenames_short = list(itertools.compress(filenames_short, in_json))
    id_cols = [settings[f]["document_column"] for f in filenames_short]

    connect = sqlite3.connect("datasets.sql")

    c = connect.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS data (filename text, id text, contents text)''')

    for filename, shortname, col in zip(filenames, filenames_short, id_cols):
        print("Adding file {}:".format(filename))

        if (delete):
            c.execute('''DELETE FROM data WHERE filename = :name''', {"name": shortname})

        csv_reader = csv.reader(open(filename, encoding="utf8", errors="ignore"))
        csv_reader.__next__()  # Skip header

        i = 0

        for row in csv_reader:
            id_val = row[col]

            sys.stdout.write("\033[K\rWriting row #{}: {}".format(i, id_val))

            c.execute('''INSERT OR IGNORE INTO data (filename, id, contents) VALUES (:filename, :id, :contents)''',
                      {"filename": shortname, "id": id_val, "contents": json.dumps(row)})

            i += 1

        print()

    connect.commit()
