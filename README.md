# Anton and Connor's Final CS127 Project

## Structure of the Project

 - Flask Interface
   - Home page
     - Search bar
     - Choice between multiple datasets
   - Display results post enter
   - Results Page
     - Search bar on top
     - Lists relevant documents w/ a bit of information (depending on dataset possibly)
     - A way to navigate back to Home
   - Document info page
     - Grep-like searching through the document
     - Displaying the document with highlighting the results.
       - List amount of word appearance
     - Statistics about the document (some basic stat analysis)
     - A way to navigate back to Home or Results.
   - Host on Connor’s website (cs-project.connorwadefitzgerald.com)
 - Core
   - Inverse Index Generator
   - Query Parser
   - Sentiment Analysis
   - Stemming
   - Smart search algorithm
     - Whole phrase
     - Contained individually within
     - Parts of phrase together or individually
   - Document statistic generation
   - Caching (SQLite)
