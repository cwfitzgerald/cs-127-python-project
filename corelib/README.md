# corelib  

Core libraries managing the database/query engine.  
  
## Components  
 - `import corelib.add_dataset as ad` function for adding csv files to the database  
 - `import corelib.database_interface as db` functions for accessing the database  
 - `import corelib.iindex as iindex` function for doing iindex queries  
 - `import corelib.query_parser as parser` functions for lexing and parsing search queries  
 - `import corelib.query_processor as processor` function for evaluating queries  
  
The server will only need db, parser, and processor to do all of it's duties. Each function is described below, using the aliases used above.  

## Server use-case
  
### Running Queries
  
To take a query, parse it, then get the results, run these functions
  
```python  
tokens = parser.lex_query(query)  
tree = parser.parse_query(tokens)  
results = processor.run_parsed_query(dataset_name, tree)  
```
  
The results will be in the following format:  
```python  
{document_id : [(submatch_column,   
                 submatch_start_offset,   
                 submatch_stop_offset (exclusive)  
                 )...]}  
```
  
### Getting document text
  
To find the full document text, run these functions
  
```python  
dataset_id = db.get_dataset_id(dataset_name)  
column_list = db.lookup_data_id(dataset_id, document_id)  
```
  
The results will be in a list of columns, each column being the text within it. You may use the submatch_column to index into this array.

### Paging through documents

To page through the documents in a dataset you can use the following functions

```python
dataset_id = db.get_dataset_id(dataset_name)  
data_min, data_max = db.lookup_data_range(dataset_id)

# only an example use
for start in range(data_min, data_max, 10):
    # one loop per page
    for content in db.iterate_over_file(dataset_id, start, start + 10):
        # do stuff with the content
```

### Find if dataset is in the database

```python
for dataset, set in db.settings.items():
    # loop through all known datasets
    if (db.data_rows(dataset)):
        # dataset in database
```
  
## Reference  
  
### add_dataset  
  
 - `ad.add_csv_to_database(filenames, delete=False)`  
   **inputs:**  
   filenames - A list of csv files to add to the database.  
   delete    - Deletes all rows that match the filename before insertion.  
   **output:**  
   None  
  
### database_interface  
  
 - `db.get_dataset_id(dataset_name)`  
   **inputs:**  
   dataset_name - Name of the dataset  
   **output:**  
   int of the id number for the dataset  
  
 - `db.data_rows(dataset_name)`  
   **inputs:**  
   dataset_name - Name of the dataset  
   **output:**  
   int of the amount of rows (documents) in the dataset  
  
 - `db.iindex_rows(dataset_name)`  
   **inputs:**  
   dataset_name - Name of the dataset  
   **output:**  
   int of the amount of rows (keywords) in the iindex database for that dataset  
  
 - `db.iterate_over_file(dataset_id, start=None, end=None)`  
   **inputs:**  
   dataset_id - id of the dataset  
   start - start key number to iterate over (inclusive)  
   end - end key number to iterate over (exclusive)  
   **output:**  
   Generator expression that will iterate over the contents of the documents  
   **notes:**  
   The range of valid key numbers for a dataset can be gotten with `db.lookup_data_range()`  
  
 - `db.lookup_data_id(dataset_id, ident)`  
   **inputs:**  
   dataset_id - id of the dataset  
   ident - the id of the document you are looking for  
   **output:**  
   Contents of the document searching for  
   **notes:**  
   All documents are referred to by their identifier.  
  
 - `db.lookup_iindex_id(dataset_id, ident)`  
   **inputs:**  
   dataset_id - id of the dataset  
   ident - the id of the iindex search you are looking for  
   **output:**  
   Documents the search was contained in  
   **notes:**  
   All documents are referred to by their identifier.  
   The 

 - `db.lookup_data_range(dataset_id)`  
   **inputs:**  
   dataset_id - id of the dataset  
   ident - the id of the iindex search you are looking for  
   **output:**  
   Documents the search was contained in.  
   **notes:**  
   All documents are referred to by their identifier.  
  
 - `db.build_iindex_database(filename)`  
   **inputs:**  
   dataset_id - filename to build the iindex database for  
   **output:**  
   None  
  
 - `db.translate_string(dataset_id, string)`  
   **inputs:**  
   dataset_id - id of the dataset  
   string - single word search query to get the iindex id for  
   **output:**  
   int with the iindex id of the search  

### iindex  
  
 - `iindex.iindex_search(dataset_name, search_term)`  
   **inputs:**  
   dataset_name - name of the dataset  
   search_term - single/multiple word search query to find the document list for  
   **output:**  
   dictionary with the following format   
   `{document_id : [(submatch_column, submatch_start_offset, submatch_stop_offset (exclusive))...]}`  
   **notes:**  
   If the returned submatches are (-1, -1, -1) then they are matches that have no location (normally part of a not match)  
  
### query_parser  
  
 - `parser.lex_query(query)`  
   **inputs:**  
   query - a text query to lex  
   **output:**  
   list of tokens to be passed to the parser  

 - `parser.parse_query(token_list)`  
   **inputs:**  
   token_list - a token list to be parsed  
   **output:**  
   anytree tree describing the search


### query_processor  
  
 - `processor.run_parsed_query(dataset_name, query_tree)`  
   **inputs:**  
   dataset_name - name of the dataset to search in  
   query_tree - the parsed query tree to execute  
   **output:**  
   dictionary with the following format   
   `{document_id : [(submatch_column, submatch_start_offset, submatch_stop_offset (exclusive))...]}`  
   **notes:**  
   If the returned submatches are (-1, -1, -1) then they are matches that have no location (normally part of a not match)  
  

### Note:  
  
Use this regex to add two spaces to the end of each line: (?<\!\\s\\s)\n(?\!\\n\)  
