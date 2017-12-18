import corelib.database_interface as db
import corelib.query_processor as qp
from flask import Flask, render_template, request
app = Flask(__name__)

##Temporary list of data list filenames.
##Will pull from actual file structure when necessary.
csv_list = [("Bus Breakdowns",'bus_breakdowns.csv'), ("Offenders", 'offenders.csv')]

@app.route("/")
def main_page():
    return render_template('main.html', csv_list = csv_list)


@app.route("/fileres", methods=['GET', 'POST'])
def res_page():
    selected = request.form.get('dataset_selection')
    search_term = request.form.get('search_term')
    ##me trying to run the entry dictionary
    entry_dict = qp.run_parsed_query("bus_breakdowns.csv", search_term)
    return(str(selected + "\n" + search_term))

@app.route("/filedisp", methods=['GET', 'POST'])

app.run(debug=True, host = '0.0.0.0', port = 8000)
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
