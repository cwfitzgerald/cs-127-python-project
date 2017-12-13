import anytree
import corelib.database_interface as db
import corelib.iindex as iindex
import corelib.query_parser as parser


def run_parsed_query(dataset_id, tree_head):
    return _run_query_node(dataset_id, tree_head)


def _run_query_node(dataset_id, node):
    if (node.token == parser.TokenType.QUOTED_TERM):
        _run_query_term(dataset_id, node)
    elif (node.token == parser.TokenType.UNQUOTED_TERM):
        _run_query_term(dataset_id, node)
    elif (node.token == parser.TokenType.AND):
        _run_query_and(dataset_id, node)
    elif (node.token == parser.TokenType.OR):
        _run_query_or(dataset_id, node)
    elif (node.token == parser.TokenType.NOT):
        _run_query_not(dataset_id, node)
    elif (node.token == parser.TokenType.EXPRESSION):
        pass  # error
    else:
        pass  # error


def _run_query_term(dataset_id, node):
    return iindex.iindex_search(dataset_id, node.token[1])


def _run_query_not(dataset_id, node):
    results = _run_query_node(dataset_id, node.children[0])
    query_documents = [k for k in results.keys()]

    min_val, max_val = db.lookup_data_range(dataset_id)
    matches = {val: (True, ()) for doc_id in range(min_val, max_val) if doc_id not in query_documents}
    return matches
