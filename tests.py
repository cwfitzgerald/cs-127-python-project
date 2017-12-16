import anytree
import corelib.iindex as iindex
import corelib.query_parser as parser
import corelib.query_processor as processor
import pprint

pprint.pprint(iindex.iindex_search("gutenberg.csv", "good morning"))
pprint.pprint(iindex.iindex_search("gutenberg.csv", "god"))
pprint.pprint(iindex.iindex_search("gutenberg.csv", "allah"))
pprint.pprint(iindex.iindex_search("gutenberg.csv", "supreme court"))

tokens = parser.lex_query("(allah AND supreme court)")
parsed_query = parser.parse_query(tokens)

print(anytree.RenderTree(parsed_query).by_attr("name"))

pprint.pprint(processor.run_parsed_query("gutenberg.csv", parsed_query))
