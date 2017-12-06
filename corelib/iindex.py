#!/usr/bin/env python3

# Here is the core library code that forms the basis of my little search engine
# This file is imported by various other programs that use it for doing searches
# The functions here are generic so they can be used to parse many-a csv

# For reference a set is like a list, but it is unordered, and is unique - there is only
# ever one copy of a value at any one time

import collections
import database_interface as db
import functools
import itertools
import json
import operator
import os           # For path manipulations
import pickle
import pprint
import re
import sys


def iindex_search(search_term):
    '''
    inputs: search_term     - a string telling what to search for
    output: a set of all resulting document name
    '''


def OLD_SIGSEGV_iindex_build_csv(filename):
    '''
    inputs: filename        - csv to inspect
            document_column - column of csv to use as the name of the "document"
            data_columns    - list of column indices to use as data. None (default) means all of them
            header          - if csv file has a row for a header
            split           - character to split columns by
            filt            - function that will be called on each element in csv
                              string -> string
    output: dicitonary mapping each data member to the set of documents that they are a part of
    '''

    # The dictionary should initialize the value of any new key to an empty set
    # A lambda is a mini function that returns what is to the right of the colon
    d = collections.defaultdict(lambda: set())

    word_splitter = re.compile('[\W0-9]+', re.UNICODE)

    document_column = db.settings[filename]["document_column"]
    data_columns = db.settings[filename]["data_columns"]
    dataset_id = db.settings[filename]["id"]

    # Open the file
    db.create_iindex_database(dataset_id, True)

    # Go through each row in the csv
    for ident, row in itertools.islice(db.iterate_over_file(filename), 0, 250):
        sys.stdout.write("Adding iindex nodes for {}:{}: ".format(filename, ident))
        # If data_columns is None (the default) we want all columns but the
        # document_column to be used as a key. We get an array of the contents.
        if data_columns is None:
            # Slice around the document_column
            keys = row[:document_column] + row[document_column + 1:]

        # If we are passed a list for data columns, we want to get the values
        # of all the appropriate rows.
        elif isinstance(data_columns, list):
            # We need to treat single columns differently to ensure the keys are list
            # of only one item. This assumption is throughout the rest of the function
            if len(data_columns) > 1:
                # operator.itemgetter(*list_of_indices)(array) is a fancy way of getting a list of
                # return values from indexing into the array multiple times. Equivilant to the following:
                # keys = []
                # for i in data_columns:
                #     keys += row[i]
                keys = operator.itemgetter(*data_columns)(row)
            else:
                # Get the only needed data column, but put it in to a list of 1. This is done by the
                # outside brackets that seemingly do nothing productive.
                keys = [row[data_columns[0]]]

        # If we are passed a single number in data_columns it will fall here.
        # We must still ensure keys is an array for later processing
        else:
            keys = [row[data_columns]]

        array_of_split_keys = [word_splitter.split(val.lower()) for val in keys]

        # Array_of_split_keys is an array of arrays, so we need to flatten it from a 2D array
        # to a 1D array. itertools.chain.from_iterable does this.
        keys = itertools.chain.from_iterable(array_of_split_keys)

        # Grab the data that we will act is the document name
        document_data = ident

        # Add each key to point to the document
        keys = list(keys)

        for k in keys:
            d[k].add(document_data)

        # pprint.pprint(keys)

        sys.stdout.write("{} keys added: ".format(len(keys)))
        sys.stdout.write("{} keys total.\n".format(len(d.keys())))

        # break

    translation = {}

    # Return the inverse index
    count = 0
    for key, values in d.items():
        int_key = db.add_to_iindex_database(dataset_id, values)
        translation[key] = int_key
        if count % 1000 == 0:
            sys.stdout.write("Adding key \'{}\' -> {} -> {} documents\n".format(key, int_key, len(values)))
            sys.stdout.flush()
        count += 1

    tf = open(db.translations, 'a+')
    tf.seek(0)
    translation_file = json.load(tf)
    translation_file[dataset_id] = translation
    json.dump(translation_file, open(db.translations, 'w'))

    db.commit()

    return d


if __name__ == "__main__":
    def filter_non_alphanumeric(x):
        return "".join([v for v in x.lower() if ('a' <= v <= 'z' or
                                                 '0' <= v <= '9'
                                                 )]).strip()

    # print(["{}, {}".format(x, str(x) <= '1') for x in range(10)])
    offenddict = iindex_build_csv("gutenberg.csv")

    offenddict = {key: list(value) for key, value in offenddict.items()}

    # pprint.pprint(offenddict)

    json.dump(offenddict, open("test.json", "w"), indent=4)

    # result = iindex_search(offenddict, "Sorry God love", split=' ', filt=filter_non_alphanumeric)

    # pprint.pprint(result)
