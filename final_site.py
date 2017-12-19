import corelib.database_interface as db
import corelib.query_processor as processor
import corelib.query_parser as parser
import itertools
from flask import Flask, render_template, request, session
#from flask.ext.session import Session
app = Flask(__name__, template_folder="flask_data/templates", static_folder="flask_data/static")
app.secret_key = "hello"
#SESSION_TYPE = 'redis'
#app.config.from_object(__name__)
#Session(app)

# Temporary list of data list filenames.

# Human Readable list of CSV Datasets (Hardcoded)
csv_list = [("Bus Breakdowns", 'bus_breakdowns.csv'), ("Offenders", 'offenders.csv'), ("Gutenberg (ALL)", 'gutenberg.csv'), ('Schools', 'schools.csv')]

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
    entry_dict = processor.run_parsed_query(str(selected), tree)
    print("\n\n", entry_dict, "\n\n")

    # Create list of relevant 'file' id's
    key_list = []
    value_list = []
    for key, value in entry_dict.items():
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

    #Create data to be passed
    for key, location_tup in itertools.zip_longest(key_list, value_list):
        #Create list of all columns in entry
        entry_column_list = db.lookup_data_id(dataset_id, key)

        #Create entry identifier based on document_column
        entry_ident = entry_column_list[doc_column]  # WILL BE PASSED TO HTML

        #Create search term location preview in entry.
        pre_prev_ind = location_tup[0][1] - 15
        if (pre_prev_ind < 0):
            pre_prev_ind = 0
        end_prev_ind = location_tup[0][2] + 40
        if (end_prev_ind > len(entry_column_list[location_tup[0][0]])):
            end_prev_ind = len(entry_column_list[location_tup[0][0]])

        pre_prev = "..." + entry_column_list[location_tup[0][0]][pre_prev_ind : location_tup[0][1]]
        word_prev = entry_column_list[location_tup[0][0]][location_tup[0][1] : location_tup[0][2]]
        end_prev = entry_column_list[location_tup[0][0]][location_tup[0][2] : end_prev_ind]
        # prev = "..." + entry_column_list[location_tup[0][0]][pre_prev_ind : end_prev_ind] # WILL BE PASSED TO HTLM
        preview_data.append( [entry_ident, (pre_prev, word_prev, end_prev)] )

    # Create list of all text in individual 'file' entry
    dataset_id = db.get_dataset_id(str(selected))
    print("Dataset ID:", dataset_id, "\n")
    column_list = db.lookup_data_id(dataset_id, key_list[0])
    print("Column List:", column_list)

    return render_template('filelist.html', preview_data = preview_data, rel_entry_type = relevant_entry_col)
    #return(str(selected + "\n" + search_term) + stringhello)



@app.route("/resultdisp/<int:entry_num>", methods=['GET', 'POST'])
def resultdisp(entry_num):
    entry_dict = session.get('entry_dict')
    document_id_list = session.get('doc_ids')
    return str(entry_num)


    print("\n\n\n\n\n")
    print("PRINTING ENTRY DICT IN RESULT DISP")
    print("\n\n")
    print(entry_dict)
    print(document_id_list)
    #dict1 = session.get('entry_dict', None)
    #search_entry = session.get('search', None)
    #dataset_id = db.get_database_id(dataset_name)
    #column_list = db.lookup_data_id(dataset_id, document_id)
    return "hello"

"""
@app.route('/set/')
def set():
    session['key'] = 'value'
    return 'ok'

@app.route('/get/')
def get():
    return session.get('key', 'not set')
"""
"""
@app.route('/a')
def a():
    session['my_var'] = 'my_value'
    return redirect(url_for('b'))

@app.route('/b')
def b():
    my_var = session.get('my_var', None)
    return my_var
"""
app.run(debug=True, host='0.0.0.0', port=8000, threaded=False)
#####################

"""#!/usr/bin/env python
from flask import Flask, flash, redirect, render_template, \
     request, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template(
        'index.html',
        data=[{'name':'red'}, {'name':'green'}, {'name':'blue'}])

@app.route("/test" , methods=['GET', 'POST'])
def test():
    select = request.form.get('comp_select')
    return(str(select)) # just to see what select is

if __name__=='__main__':
    app.run(debug=True)
"""
