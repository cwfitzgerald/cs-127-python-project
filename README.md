# Anton and Connor's Final CS127 Project

## Project Description

Our project is a web application for searching key terms within multiple datasets. We plan to implement basic sentiment analysis and stemming, along with a smart search algorithm for multiple key terms. Our web page will allow for easy navigation between documents and results, provide document statistics relevant to the search and highlight all results for the user. In addition, we plan to implement caching for elevated performance of repetitive searches.

## Setup Server

Server setup is simple and takes place in two steps. First you must download all the datasets and build the database. This is handled by setup_coordinator.py.

```
./setup_coordinator.py
```

This will make sure you have all the dependencies you need and builds all the c++ code.

Then you can run 

```
./server.py
```

which will launch the server on localhost:8000.

## How to Search

Choose a dataset with the dropdown. You may then search for things with the following operators (in all caps)

```
AND
OR
NOT
```

You may also use quotation marks for an exact match or parathesis for grouping your search operators. 

## Known Issue / Recommendation
* Generally whole word (>2 letter) search terms tend to provide the best results.
* Do not search a two digit number in the Bus Breakdowns dataset, it will take a very long time to load.

## Structure of the Project

 - Flask Interface
   - Home page
     - Search bar
     - Choice between multiple datasets
   - Display results post enter
   - Results Page
     - Search bar on top
   - Document info page
 - Core
   - Inverse Index Generator
   - Query Parser
   - Smart search algorithm
     - Whole phrase
     - Contained individually within
     - Parts of phrase together or individually
   - Caching (Memoization)

## Folder Structure

 - corelib
   - the core libraries that make things work
 - flask
   - all the data that flask needs
 - datasets
   - storage location for index.json and the actual database

