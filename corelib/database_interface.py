import pickle
import json
import pickletools
import os
import sqlite3
import itertools
import threading


database = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../datasets/datasets.sql")
translations = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../datasets/translations.json")


class ThreadLocalConnection(threading.local):
    connection = connection = sqlite3.connect(database)


tlc = ThreadLocalConnection()

settings = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../datasets/index.json")))


def iterate_over_file(dataset_name):
    cursor = tlc.connection.cursor()

    dataset_name = os.path.basename(dataset_name)

    dataset_id = settings[dataset_name]["id"]

    cursor.execute('''SELECT id, contents FROM data WHERE filename = :filename''',
                   {"filename": dataset_id})

    while True:
        res = cursor.fetchone()

        if (res is None):
            break

        ident = res[0]

        try:
            contents = pickle.loads(res[1], encoding='utf8', errors="ignore")
        except UnicodeDecodeError:
            print("The ****in decoder don't work")
            continue

        yield (ident, contents)


def lookup_id(dataset_name, id):
    cursor = tlc.connection.cursor()

    dataset_name = os.path.basename(dataset_name)

    dataset_id = settings[dataset_name]["id"]

    cursor.execute('''SELECT contents FROM data WHERE filename = :filename and id = :id''',
                   {"filename": dataset_id})

    res = cursor.fetchone()

    if (res is None):
        return ValueError("No id found")

    contents = pickle.loads(res[0], encoding='utf8', errors="ignore")

    return contents


def create_iindex_database(dataset_id, clean=False):
    cursor = tlc.connection.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS iindex (file_id integer, key integer primary key, contents text)''')

    if clean:
        cursor.execute('''DELETE FROM iindex WHERE file_id = :file_id''',
                       {"file_id": dataset_id})

    tlc.connection.commit()


def add_to_iindex_database(dataset_id, document_ids, clean=False):
    cursor = tlc.connection.cursor()

    doclist = list(document_ids)

    cursor.execute('''INSERT OR REPLACE INTO iindex (file_id, contents) VALUES(:file_id, :contents)''',
                   {"file_id": dataset_id, "contents": pickle.dumps(doclist)})

    return cursor.lastrowid


def commit():
    tlc.connection.commit()


if __name__ == "__main__":
    for ident, content in itertools.islice(iterate_over_file("gutenberg.csv"), 0, 100):
        print("id: {} - content: {}".format(ident, content[1]))
