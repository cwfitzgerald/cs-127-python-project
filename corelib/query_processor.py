import anytree
import corelib.iindex as iindex
import corelib.query_parser as parser


def run_parsed_query(dataset_id, tree_head):
    return _run_query_node(dataset_id, tree_head)


def _run_query_nonde(dataset_id, node):
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
