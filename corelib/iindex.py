#!/usr/bin/env python3

import corelib.database_interface as db
import itertools
import functools
import operator
import re


def iindex_search(dataset_name, search_term):
    '''
    inputs: dataset_id  - id of dataset to search through
            search_term - a string telling what to search for
    output: a set of all resulting document name
    '''

    dataset_id = db.settings[dataset_name]["id"]
    word_separator_regex = db.settings[dataset_name]["pyregex"]

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

        match_pairs.append((match, full_text, submatches))

    return match_pairs
