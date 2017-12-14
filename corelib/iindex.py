#!/usr/bin/env python3

import corelib.database_interface as db
import itertools
import functools
import operator
import re


def iindex_search(dataset_id, search_term):
    '''
    inputs: dataset_id  - id of dataset to search through
            search_term - a string telling what to search for
    output: (document id : positive/negative, [(column of match, submatch start, submatch end)...])
    '''

    lookup_id = [db.translate_string(dataset_id, term) for term in search_list]
    matches = [set(db.lookup_iindex_id(dataset_id, ident)) for ident in lookup_id]

    regex_prog = re.compile(word_separator_regex.join(search_list), re.UNICODE | re.IGNORECASE)

    unique_matches = functools.reduce(operator.and_, matches)

    match_pairs = {}
    # search each match for the string
    for match in unique_matches:
        full_text = db.lookup_data_id(dataset_id, match)

        submatches = [[(i, submatch.start(), submatch.end()) for submatch in regex_prog.finditer(column)]
                      for i, column in enumerate(full_text) if i in db.settings[dataset_name]["data_columns"]]

        submatches = list(itertools.chain.from_iterable(submatches))

        if len(submatches) > 0:
            match_pairs[match] = (True, submatches)

    return match_pairs
