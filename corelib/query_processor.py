import corelib.database_interface as db
import corelib.iindex as iindex
import corelib.query_parser as parser
import collections
import functools
import operator


def run_parsed_query(dataset_name, tree_head):
    return _run_query_node(dataset_name, db.settings[dataset_name]["id"], tree_head)


def _run_query_node(dataset_name, dataset_id, node):
    if (node.token[0] == parser.TokenType.QUOTED_TERM):
        return _run_query_term(dataset_name, dataset_id, node)
    elif (node.token[0] == parser.TokenType.UNQUOTED_TERM):
        return _run_query_term(dataset_name, dataset_id, node)
    elif (node.token[0] == parser.TokenType.AND):
        return _run_query_and(dataset_name, dataset_id, node)
    elif (node.token[0] == parser.TokenType.OR):
        return _run_query_or(dataset_name, dataset_id, node)
    elif (node.token[0] == parser.TokenType.NOT):
        return _run_query_not(dataset_name, dataset_id, node)
    elif (node.token[0] == parser.TokenType.EXPRESSION):
        raise ValueError("Unexpected EXPRESSION")
        pass  # error
    else:
        raise ValueError("Unexpected I don't know")
        pass  # error


def _run_query_term(dataset_name, dataset_id, node):
    ans = iindex.iindex_search(dataset_name, node.token[1])
    print(node.token[1], ans)
    return ans


def _run_query_not(dataset_name, dataset_id, node):
    results = _run_query_node(dataset_name, dataset_id, node.children[0])
    query_documents = [k for k in results.keys()]

    min_val, max_val = db.lookup_data_range(dataset_id)
    matches = {doc_id: () for doc_id in range(min_val, max_val) if doc_id not in query_documents}
    return matches


def _run_query_or(dataset_name, dataset_id, node):
    result_sets = [_run_query_node(dataset_name, dataset_id, child) for child in node.children]

    merged = collections.defaultdict(lambda: [])

    for r in result_sets:
        for doc, submatches in r.items():
            for submatch in submatches:
                merged[doc].append(submatch)

    return merged


def _run_query_and(dataset_name, dataset_id, node):
    result_sets = [_run_query_node(dataset_name, dataset_id, child) for child in node.children]

    documents = functools.reduce(operator.and_, [set(result.keys()) for result in result_sets])

    merged = collections.defaultdict(lambda: [])

    for r in result_sets:
        for doc, submatches in r.items():
            if doc in documents:
                if len(submatches) > 0:
                    for submatch in submatches:
                        merged[doc].append(submatch)
                else:
                    merged[doc].append((,))

    return merged
