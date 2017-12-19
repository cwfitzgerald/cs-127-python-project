import cachetools.func
import corelib.util as util
import csv
import ctypes
import itertools
import json
import os
import pickle
import pickletools
import sqlite3
import threading

csv.field_size_limit(2**31 - 1)

database_path = util.relative_path(__file__, "../datasets/datasets.sql")
settings = json.load(open(util.relative_path(__file__, "../datasets/index.json")))

helper_dll_path = util.relative_path(__file__, "libdatabase.so")
helper_dll = None


def setup_dll():
    dll = ctypes.CDLL(helper_dll_path)

    dll.build_iindex_database.argtypes = [ctypes.c_char_p]
    dll.build_iindex_database.restype = None
    dll.translate_string.argtypes = [ctypes.c_int, ctypes.c_char_p]
    dll.translate_string.restype = ctypes.c_int
    dll.load_runtime_data.restype = None

    return dll


@util.run_once
def create_tables():
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS data (file_id integer, key integer primary key, contents text)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS iindex (file_id integer, key integer primary key, contents text)''')

    connection.commit()


@cachetools.func.lru_cache(16)
def get_dataset_id(dataset_name):
    return settings[dataset_name]["id"]


@cachetools.func.lru_cache(16)
def get_dataset_name(dataset_id):
    return (name for name, data in settings.items() if data["id"] == dataset_id).__next__()


@cachetools.func.lru_cache(16)
def _rows(table, dataset_name):
    create_tables()
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    dataset_name = os.path.basename(dataset_name)
    dataset_id = get_dataset_id(dataset_name)

    cursor.execute('''SELECT count(*) FROM {} WHERE file_id = :file_id'''.format(table),
                   {"table": table, "file_id": dataset_id})

    res = cursor.fetchone()

    if res is None:
        return 0

    connection.commit()

    return res[0]


def data_rows(dataset_name):
    return _rows("data", dataset_name)


def iindex_rows(dataset_name):
    return _rows("iindex", dataset_name)


def iterate_over_file(dataset_id, start=None, end=None):
    create_tables()
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    cursor.execute('''SELECT key, contents FROM data WHERE file_id = :file_id {} {}'''
                   .format("and key >= :start" if start is not None else "",
                           "and key < :end" if end is not None else ""),
                   {"file_id": dataset_id, "start": start, "end": end})

    while True:
        res = cursor.fetchone()

        if (res is None):
            break

        ident = res[0]

        try:
            contents = json.loads(res[1])
        except UnicodeDecodeError:
            print("The ****in decoder don't work")
            continue

        yield (ident, contents)

    connection.commit()


@cachetools.func.lru_cache(128)
def lookup_data_id(dataset_id, ident):
    if ident is None:
        return []

    create_tables()
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    cursor.execute('''SELECT contents FROM data WHERE file_id = :file_id and key = :ident''',
                   {"file_id": dataset_id, "ident": ident})

    res = cursor.fetchone()

    if (res is None):
        raise ValueError("No data id found")

    contents = json.loads(res[0])

    connection.commit()

    return contents


@cachetools.func.lfu_cache(256)
def lookup_iindex_id(dataset_id, ident):
    if ident is None:
        return []

    create_tables()
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    cursor.execute('''SELECT contents FROM iindex WHERE file_id = :file_id and key = :ident''',
                   {"file_id": dataset_id, "ident": ident})

    res = cursor.fetchone()

    if (res is None):
        print(dataset_id, ident)
        raise ValueError("No iindex id found")

    contents = json.loads(res[0])

    connection.commit()

    return contents


@cachetools.func.lru_cache(16)
def lookup_data_range(dataset_id):
    create_tables()
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    cursor.execute('''SELECT max(key) FROM data WHERE file_id = :file_id''',
                   {"file_id": dataset_id})

    res_max = cursor.fetchone()

    cursor.execute('''SELECT min(key) FROM data WHERE file_id = :file_id''',
                   {"file_id": dataset_id})

    res_min = cursor.fetchone()

    connection.commit()

    return (res_min[0], res_max[0] + 1)


@util.run_once
def load_runtime_data():
    global helper_dll
    create_tables()
    if helper_dll is None:
        helper_dll = setup_dll()

    helper_dll.load_runtime_data()


def build_iindex_database(filename):
    global helper_dll
    create_tables()
    if helper_dll is None:
        helper_dll = setup_dll()

    helper_dll.build_iindex_database(bytes(filename, encoding='utf8'))


# Small cache to prevent calling off to C++ library
@cachetools.func.lfu_cache(256)
def translate_string(dataset_id, string):
    global helper_dll
    create_tables()
    load_runtime_data()
    if helper_dll is None:
        helper_dll = setup_dll()

    res = helper_dll.translate_string(ctypes.c_int(dataset_id), bytes(string, encoding='utf8'))

    if res == -1:
        return None
    return res
