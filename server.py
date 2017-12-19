#!/usr/bin/env python3

import corelib.database_interface as db
import corelib.query_processor as processor
import corelib.query_parser as parser
import itertools
import operator
import collections
from flask import Flask, render_template, request, session

# from flask.ext.session import Session
app = Flask(__name__, template_folder="flask_data/templates", static_folder="flask_data/static")
app.secret_key = "hello"
# SESSION_TYPE = 'redis'
# app.config.from_object(__name__)
# Session(app)

# Temporary list of data list filenames.

# Human Readable list of CSV Datasets (Hardcoded)
csv_list = [("Bus Breakdowns", 'bus_breakdowns.csv'), ("Offenders", 'offenders.csv'),
            ("Gutenberg (ALL)", 'gutenberg.csv'), ('Schools', 'schools.csv')]


@app.route("/")
def main_page():
    """
    list1 = []
    for dataset, dataset_properties in db.settings.items():
        # loop through all known datasets
        if (db.data_rows(dataset)):
            list1.append(dataset)
    """

    return render_template('main.html', csv_list=csv_list)


@app.route("/fileres", methods=['GET', 'POST'])
def res_page():

    # Pull form data from dropdown menu and search input
    selected = request.form.get('dataset_selection')
    search_term = request.form.get('search_term')
    print(search_term)
    print("\n\n\nPRINTING SELECTED DATASET VALUE", selected, "\n\n")

    # Parse search term and create result dictionary
    tokens = parser.lex_query(str(search_term))
    tree = parser.parse_query(tokens)

    # Create dictionary of all relevant entries and locations
    try:
        entry_dict = processor.run_parsed_query(str(selected), tree)
    except ValueError:
        return render_template('invalid.html', search_term=str(search_term))
    print("\n\n", entry_dict, "\n\n")

    if (len(entry_dict) == 0):
        return render_template('not_found.html', search_term=str(search_term), selected=str(selected))
    # Create list of relevant 'file' id's
    key_list = []
    value_list = []
    for key, value in sorted(entry_dict.items(), key=operator.itemgetter(0)):
        key_list.append(key)
        value_list.append(value)

    # Create session entries for full entry dict and 'doc' id's
    session['entry_dict'] = entry_dict
    session['doc_ids'] = key_list

    print("\n\n")
    print("KeyList")
    print(key_list, "\n\n")
    print("Value List")
    print(value_list, "\n\n")

    # Create dataset_id
    dataset_id = db.get_dataset_id(str(selected))
    print("Dataset ID:", dataset_id, "\n")

    # Create list of tuples with file "name" and data of where relevant
    # search term was found. Differentiated per dataset.
    # return str(db.settings["offenders.csv"]["id"])

    preview_data = []
    doc_headers = db.settings[str(selected)]["headers"]
    print("doc_headers\n", doc_headers, "\n")
    doc_column = int(db.settings[str(selected)]["document_column"])
    print("doc_column\n", doc_column, "\n")
    relevant_entry_col = doc_headers[doc_column]
    print("relevant_entry_col\n", relevant_entry_col, "\n")

    # Create data to be passed
    for key, location_tup in itertools.zip_longest(key_list, value_list):
        # Create list of all columns in entry
        entry_column_list = db.lookup_data_id(dataset_id, key)

        # Create entry identifier based on document_column
        entry_ident = entry_column_list[doc_column]  # WILL BE PASSED TO HTML

        # Create search term location preview in entry.
        """
        [
            [(8, 23, 26)],
            [(8, 364, 367)],
            [(8, 493, 496)],
            [(8, 37, 40)],
            [(8, 8, 11), (8, 268, 271), (8, 409, 412), (8, 461, 464), (8, 565, 568)]
        ]
        location_tup = [(8, 23, 26)]
        location_tup = [(8, 8, 11), (8, 268, 271)]

        amount_of_first_column_occurence = 1
        amount_of_tups_in_location_tup = len(location_tup)
        temp = location_tup[0][0]
        if (amount_of_tups_in_location_tup > 1):
            for x in range(1, amount_of_tups_in_location_tup):
                if (location_tup[x][0] = temp):
                    amount_of_first_column_occurence += 1
                temp = location_tup[0][0]
        temp2 = location_tup[0][2]
        """

        pre_prev_ind = location_tup[0][1] - 15
        if (pre_prev_ind < 0):
            pre_prev_ind = 0

        # If more than one instance
        """
        if (len(location_tup[0]) > 1)
        """
        end_prev_ind = location_tup[0][2] + 40

        if (end_prev_ind > len(entry_column_list[location_tup[0][0]])):
            end_prev_ind = len(entry_column_list[location_tup[0][0]])

        pre_prev = "..." + entry_column_list[location_tup[0][0]][pre_prev_ind: location_tup[0][1]]
        word_prev = entry_column_list[location_tup[0][0]][location_tup[0][1]: location_tup[0][2]]
        end_prev = entry_column_list[location_tup[0][0]][location_tup[0][2]: end_prev_ind]

        # prev = "..." + entry_column_list[location_tup[0][0]][pre_prev_ind : end_prev_ind] # WILL BE PASSED TO HTLM
        preview_data.append([entry_ident, (pre_prev, word_prev, end_prev), key])

    # Create list of all text in individual 'file' entry
    dataset_id = db.get_dataset_id(str(selected))
    print("Dataset ID:", dataset_id, "\n")
    column_list = db.lookup_data_id(dataset_id, key_list[0])
    print("Column List:", column_list)

    return render_template('filelist.html', preview_data=preview_data,
                           rel_entry_type=relevant_entry_col, dataset_id=dataset_id)
    # return(str(selected + "\n" + search_term) + stringhello)


@app.route("/resultdisp/<int:dataset_id>/<int:entry_num>", methods=['GET', 'POST'])
def resultdisp(dataset_id, entry_num):
    entry_dict = session.get('entry_dict')
    document_id_list = session.get('doc_ids')
    # <span id="prev_word"></span>
    full_text = db.lookup_data_id(dataset_id, entry_num)[:]

    matches = sorted(entry_dict[str(entry_num)])

    offsets = collections.defaultdict(lambda: 0)
    for col_id, start, end in matches:
        front_tag = "<span id=\"prev_word\">"
        rear_tag = "</span>"

        taglength = len(front_tag) + len(rear_tag)

        offset = offsets[col_id]

        start += offset
        end += offset

        full_text[col_id] = full_text[col_id][:start] + front_tag + \
            full_text[col_id][start:end] + rear_tag + full_text[col_id][end:]

        offsets[col_id] += taglength

    dataset_name = db.get_dataset_name(dataset_id)

    column_getter = operator.itemgetter(*db.settings[dataset_name]["data_columns"])
    columns = column_getter(list(zip(db.settings[dataset_name]["headers"], full_text)))

    return render_template('displayfile.html', data=columns)

app.run(debug=True, host='0.0.0.0', port=8000, threaded=False)
