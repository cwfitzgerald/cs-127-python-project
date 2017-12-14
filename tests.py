import anytree
import corelib.iindex as iindex
import corelib.query_parser as parser
import corelib.query_processor as processor
import pprint

pprint.pprint(iindex.iindex_search("offenders.csv", "good morning"))
pprint.pprint(iindex.iindex_search("offenders.csv", "god"))
pprint.pprint(iindex.iindex_search("offenders.csv", "allah"))
pprint.pprint(iindex.iindex_search("offenders.csv", "supreme court"))

tokens = parser.lex_query("end OR NOT allah")
parsed_query = parser.parse_query(tokens)

print(anytree.RenderTree(parsed_query).by_attr("name"))

pprint.pprint(processor.run_parsed_query("offenders.csv", parsed_query))
