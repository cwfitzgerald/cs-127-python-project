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

    lookup_id = db.translate_string(dataset_id)
