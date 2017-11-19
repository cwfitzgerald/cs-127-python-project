from anytree import Node, RenderTree
import enum
import itertools
import pprint
import timeit


class TokenType(enum.Enum):
    QUOTED_TERM = 1    # Search term surrounded by quotes
    UNQUOTED_TERM = 2  # Array of unquoted terms
    AND = 3            # AND in all capital letters for binary and
    OR = 4             # OR in all capital letters for binary or
    NOT = 5            # NOT in all capital letters for unary not
    PAREN_L = 6        # (
    PAREN_R = 7        # )
    EXPRESSION = 8     # Container to put tokens into


def lex_query(query):
    '''
    lexes a search query into an array of tokens for the parser to parse

     input: query - The query to lex
    output: the list of tokens
    '''

    # Evaluate the query length as is constantly referred to throughout
    # the lexer and so lookup is faster
    query_length = len(query)

    token_stream = []

    # Index into the query
    i = 0

    # I have yet to be able to write an O(N) lexer that doesn't turn into a bunch of confusing control
    # flow and index thrashing. I have done my best to explain the rationalle behind this, but viewer beware
    while i < query_length:
        # Check if we're pointing to the beginning of either three
        # letter token: 'AND' or 'NOT'
        if (i + 2 < query_length):
            # Pull current caracter and next two characters
            # Adding one for the past-the-end index
            tested_string = query[i:i + 2 + 1]

            # As we break from both of these early, we must iterate i here
            # to be pointing to the character after the token we just pulled
            if (tested_string == 'AND'):
                token_stream.append((TokenType.AND,))
                i += 3
                continue

            elif (tested_string == 'NOT'):
                token_stream.append((TokenType.NOT,))
                i += 3
                continue

        # Check if we're pointing to the beginning of the two letter token: 'OR'
        if (i + 1 < query_length):
            tested_string = query[i:i + 1 + 1]

            # As we break from this early, we must iterate i here
            # to be pointing to the character after the 'OR' token
            if (tested_string == 'OR'):
                token_stream.append((TokenType.OR,))
                i += 2
                continue

        # Push parenthesis onto the stream
        if (query[i] == '('):
            token_stream.append((TokenType.PAREN_L,))

        elif (query[i] == ')'):
            token_stream.append((TokenType.PAREN_R,))

        # Ignore spaces
        elif (query[i].isspace()):
            pass

        # Grab a quoted string
        elif (query[i] in "\"'"):
            quote_used = query[i]

            i += 1
            query_text = []
            while (i < query_length) and (query[i] != quote_used):
                # Escape character is skipped and the next character is grabbed
                if (query[i] == '\\' and i + 1 < query_length):
                    i += 1
                query_text.append(query[i])
                i += 1
            token_stream.append((TokenType.QUOTED_TERM, "".join(query_text)))
        # Grab unquoted strings
        else:
            start = i
            # Unquoted string terminate with a space or parenthesis or quotes
            while (i < query_length) and (not query[i].isspace()) and (not query[i] in "()\"'"):
                i += 1
            token_stream.append((TokenType.UNQUOTED_TERM, query[start:i]))
            continue

        i += 1

    return token_stream


class TokenContainer():
    def __init__(self, token_list):
        self._location = 0
        self._length = len(token_list)
        self._token_list = token_list

    def get_next_token(self, ttype):
        if (self._location < self._length and self._token_list[self._location][0] == ttype):
            ret = self._token_list[self._location]
            self._location += 1
            return ret

    def skip_next_token(self, ttype):
        if (self._location < self._length and self._token_list[self._location][0] == ttype):
            self._location += 1
            return True
        return False


def rd_apply_parent(parent, *children):
    # Make sure everything is a list of lists
    children_2d = [c if isinstance(c, list) else [c] for c in children]
    # Flatten the 2d list
    flattened_children = itertools.chain.from_iterable([c if isinstance(c, list) else [c] for c in children])
    for child in flattened_children:
        child.parent = parent

'''
Grammar:

expr ::= or_expr
or_expr ::= and_expr | and_expr OR expr
and_expr ::= not_expr | not_expr AND expr
not_expr ::= factor | NOT factor
factor ::= term | term '(' expr ')' term
term ::= (unquoted_term | quoted_term)*
'''


def parse_query(token_list):
    parse_tree = rd_parse_expr(TokenContainer(token_list))
    clean_up_excess_expressions(parse_tree)
    rewrite_expression_groups(parse_tree)
    return parse_tree


def rd_parse_expr(token_container):
    return rd_parse_or_expr(token_container)


def rd_parse_or_expr(token_container):
    left = rd_parse_and_expr(token_container)

    if token_container.skip_next_token(TokenType.OR):
        right = rd_parse_expr(token_container)
        parent = Node("OR", token=(TokenType.OR,))

        rd_apply_parent(parent, left, right)
        return parent
    else:
        return left


def rd_parse_and_expr(token_container):
    left = rd_parse_not_expr(token_container)

    if token_container.skip_next_token(TokenType.AND):
        right = rd_parse_expr(token_container)
        parent = Node("AND", token=(TokenType.AND,))

        rd_apply_parent(parent, left, right)
        return parent
    else:
        return left


def rd_parse_not_expr(token_container):
    was_a_not = token_container.skip_next_token(TokenType.NOT)

    factor = rd_parse_factor(token_container)

    if (was_a_not):
        parent = Node("NOT", token=(TokenType.NOT,))

        rd_apply_parent(parent, factor)
        return parent
    else:
        return factor


def rd_parse_factor(token_container):
    left = rd_parse_term(token_container)

    if token_container.skip_next_token(TokenType.PAREN_L):
        expr = rd_parse_expr(token_container)
        # print(RenderTree(expr))
        if not token_container.skip_next_token(TokenType.PAREN_R):
            raise ValueError("No Matching Right Paren")

        right = rd_parse_term(token_container)

        parent = Node("EXPRESSION", token=(TokenType.EXPRESSION,))

        rd_apply_parent(parent, left, expr, right)

        return parent
    else:
        parent = Node("EXPRESSION", token=(TokenType.EXPRESSION,))

        rd_apply_parent(parent, left)

        return parent


def rd_parse_term(token_container):
    list_of_terms = []

    while True:
        token = token_container.get_next_token(TokenType.QUOTED_TERM)
        if (token is None):
            token = token_container.get_next_token(TokenType.UNQUOTED_TERM)
        # print(token_container._token_list[token_container._location:])

        if (token is None):
            break
        else:
            if token[0] == TokenType.UNQUOTED_TERM:
                list_of_terms.append(Node(token[1], token=token))
            else:
                list_of_terms.append(Node('"{}"'.format(token[1]), token=token))

    # if len(parent.children) == 0:
    #     raise ValueError("Say What")

    return list_of_terms


def clean_up_excess_expressions(tree):
    '''
    Remove nested unnessisary EXPRESSIONS in a true (when an expression just contains other expressions) and
    where an EXPRESSION holds only one child (where it is ment to hold many)

     inputs: tree - root node of the tree
    outputs: None
    '''
    # Keep calling recursivly down then start merging depth-first
    for child in tree.children:
        clean_up_excess_expressions(child)
        # Merge when there are two expressions in a row. Merge subchildren up two
        if (tree.token[0] == TokenType.EXPRESSION and (child.token[0] == TokenType.EXPRESSION)):
            for sub_child in child.children:
                sub_child.parent = tree
            child.parent = None
        # Merge when there is an EXPRESSION with one child. Merge children up to the parent of the tree
        if (tree.token[0] == TokenType.EXPRESSION and len(tree.children) == 1):
            if (tree.parent):
                child.parent = tree.parent
                tree.parent = None
            else:
                tree.name = child.name
                tree.token = child.token

                for sub_child in child.children:
                    sub_child.parent = tree

                child.parent = None


def rewrite_expression_groups(tree):
    children = tree.children

    if len(children) == 0:
        return

    for child in children:
        rewrite_expression_groups(child)

    children_all_tokens = all([child.token[0] in [TokenType.UNQUOTED_TERM, TokenType.QUOTED_TERM]
                               for child in children])
    if (tree.token[0] == TokenType.EXPRESSION and children_all_tokens and len(children) >= 2):
        # Concatentated Node
        concat_text = " ".join([child.token[1] for child in children])
        concat_node = Node('"{}"'.format(concat_text), token=(TokenType.QUOTED_TERM, concat_text))

        # And Nodes
        and_base = Node("AND", token=(TokenType.AND,))
        for child in children:
            child.parent = and_base

        # OR Nodes
        or_base = Node("OR", token=(TokenType.OR,))
        for child in children:
            Node(child.token[1], parent=or_base, token=child.token)

        if (tree.is_root):
            tree.name = "OR"
            tree.token = (TokenType.OR,)
            rewrite_root = tree
        else:
            rewrite_root = Node("OR", parent=tree.parent, token=(TokenType.OR,))
            tree.parent = None
        rd_apply_parent(rewrite_root, concat_node, and_base, or_base)

if __name__ == "__main__":
    bizzare_query = "(((Trains Planes Automobiles) AND NOT ('Ships AND Dips' AND Lips)) AND"\
                    " ((something funny happened on the way to the forum) AND NOT gallagher))"
    # lexed = lex_query(bizzare_query)

    # lexed = lex_query("((Hello AND Hi) OR NOT (Love Hate) OR NOT 'NOT AND OR HELLO!')"
    #                            "AND ((Hello Yellow) McJello)")
    lexed = lex_query("Google Sucks")
    print("lexer:")
    print(timeit.timeit("lex_query(bizzare_query)", number=1000, globals=globals()), "ms")
    pprint.pprint(lexed)

    print("\nAST:")
    print(timeit.timeit("parse_query(lexed)", number=1000, globals=globals()), "ms")
    print(RenderTree(parse_query(lexed)).by_attr("name"))
