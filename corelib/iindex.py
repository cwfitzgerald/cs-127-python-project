#!/usr/bin/env python3

# Here is the core library code that forms the basis of my little search engine
# This file is imported by various other programs that use it for doing searches
# The functions here are generic so they can be used to parse many-a csv

# For reference a set is like a list, but it is unordered, and is unique - there is only
# ever one copy of a value at any one time

import cachetools
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


@cachetools.cached(cachetools.LRUCache(1000000))
def iindex_search(dataset_id, search_term):
    '''
    inputs: dataset_id  - id of dataset to search through
            search_term - a string telling what to search for
    output: a set of all resulting document name
    '''

    search_list = search_term.split()

    lookup_id = [db.translate_string(dataset_id, term) for term in search_list]
    matches = [set(db.lookup_iindex_id(dataset_id, ident)) for ident in lookup_id]

    regex_prog = re.compile(word_separator_regex.join(search_list), re.UNICODE | re.IGNORECASE)

    unique_matches = matches[0]

    unique_matches = functools.reduce(operator.and_, matches)

    match_pairs = []
    # search each match for the string
    for match in unique_matches:
        full_text = db.lookup_data_id(dataset_id, match)

        submatches = [[(i, submatch.start(), submatch.end()) for submatch in regex_prog.finditer(column)]
                      for i, column in enumerate(full_text) if i in db.settings[dataset_name]["data_columns"]]

        submatches = list(itertools.chain.from_iterable(submatches))

        if len(submatches) > 0:
            match_pairs.append((match, submatches))
