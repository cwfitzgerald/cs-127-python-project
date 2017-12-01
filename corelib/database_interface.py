import json
import os
import sqlite3
import itertools


database = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../datasets/datasets.sql")
connection = sqlite3.connect(database)


def iterate_over_file(database_name):
    cursor = connection.cursor()

    database_name = os.path.basename(database_name)

    cursor.execute('''SELECT id, contents FROM data WHERE filename = :filename''',
                   {"filename": database_name})

    while True:
        res = cursor.fetchone()

        if (res is None):
            break

        ident = res[0]

        contents = json.loads(res[1])

        yield (ident, contents)


def lookup_id(database_name, id):
    cursor = connection.cursor()

    database_name = os.path.basename(database_name)

    cursor.execute('''SELECT contents FROM data WHERE filename = :filename and id = :id''',
                   {"filename": database_name})

    res = cursor.fetchone()

    if (res is None):
        return ValueError("No id found")

    contents = json.loads(res[0])

    return contents


if __name__ == "__main__":
    for ident, content in itertools.islice(iterate_over_file("gutenberg.csv"), 0, 100):
        print("id: {} - content: {}".format(ident, content[1]))
