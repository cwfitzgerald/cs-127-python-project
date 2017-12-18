import corelib.database_interface as db
import corelib.query_processor as processor
import corelib.query_parser as parser
from flask import Flask, render_template, request
app = Flask(__name__, template_folder="flask_data/templates", static_folder="flask_data/static")

# Temporary list of data list filenames.
# Will pull from actual file structure when necessary.
csv_list = [("Bus Breakdowns", 'bus_breakdowns.csv'), ("Offenders", 'offenders.csv')]


@app.route("/")
def main_page():
    list1 = []
    for dataset, dataset_properties in db.settings.items():
        # loop through all known datasets
        if (db.data_rows(dataset)):
            list1.append(dataset)
    return render_template('main.html', csv_list=list1)


@app.route("/fileres", methods=['GET', 'POST'])
def res_page():
    selected = request.form.get('dataset_selection')
    search_term = request.form.get('search_term')
    # me trying to run the entry dictionary
    tokens = parser.lex_query(str(search_term))
    tree = parser.parse_query(tokens)
    entry_dict = processor.run_parsed_query("offenders.csv", tree)
    print(entry_dict)
    return(str(selected + "\n" + search_term))


def get_entry_names():
    return "hello"


@app.route("/filedisp", methods=['GET', 'POST'])
def filedisp():
    return "hello"


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
