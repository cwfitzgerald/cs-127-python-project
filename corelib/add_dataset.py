import corelib.database_interface as db
import corelib.util as util
import csv
import itertools
import json
import operator
import os
import pickle
import pickletools
import sqlite3
import sys

# This method takes .csv file names as arguments and checks whether they exist in index.JSON.
# If so, creates a SQL database from the CSV file, with three columns, filename, id, and contents.
# This is in order to deal with the massive data amounts in the CSV's, and not have to
# iterate through everything in order to reach the file contents when displaying the results.


def add_csv_to_database(filenames, delete=False):
    filenames_short = list(map(os.path.basename, filenames))

    in_json = [x in db.settings for x in filenames_short]

    filenames = list(itertools.compress(filenames, in_json))
    filenames_short = list(itertools.compress(filenames_short, in_json))
    id_cols = [db.settings[f]["document_column"] for f in filenames_short]
    dataset_ids = [db.settings[f]["id"] for f in filenames_short]

    connect = sqlite3.connect(util.relative_path(__file__, "../datasets/datasets.sql"))

    c = connect.cursor()

    tty_rows, tty_columns = map(int, os.popen('stty size', 'r').read().split())

    for filename, shortname, col, dataset_id in zip(filenames, filenames_short, id_cols, dataset_ids):

        if (delete):
            c.execute('''DELETE FROM data WHERE file_id = :id''', {"id": dataset_id})
            sys.stdout.write("\t{} -- Deleting Old Records".format(filename))

        csv_reader = csv.reader(open(filename, encoding="utf8", errors="backslashreplace"))
        csv_reader.__next__()  # Skip header

        i = 0

        for row in csv_reader:
            if row[-1] == '':
                row = row[:-1]

            id_val = row[col]

            coretext = "{} -- Writing row #{}: {}".format(filename, i, id_val)
            printlen = 8 + len(coretext)
            trimval = tty_columns - printlen
            if (trimval < 0):
                coretext = coretext[:trimval]

            sys.stdout.write("\r\033[K\r\t{}".format(coretext))
            sys.stdout.flush()

            c.execute('''INSERT OR IGNORE INTO data (file_id, contents) VALUES (:file_id, :contents)''',
                      {"file_id": dataset_id, "contents": json.dumps(row)})

            i += 1

        print("\r\033[K\r\t{} -- \u001b[32;1mSuccess\u001b[0m".format(filename))

    connect.commit()


def main():
    if (sys.argv[1] in ["--delete", "-d"]):
        delete = True
    else:
        delete = False

    if (len(sys.argv) < 2):
        print("Usage: {} [--delete] [<input_csv>]*".format(sys.argv[0]))
        exit(1)

    filenames = list(map(os.path.abspath, sys.argv[2 if delete else 1:]))

    add_csv_to_database(database, delete)

if __name__ == "__main__":
    main()
