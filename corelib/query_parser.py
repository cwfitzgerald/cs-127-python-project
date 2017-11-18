import enum
from anytree import Node, RenderTree


class TokenType(enum.Enum):
    END = 0            # End of query
    QUOTED_TERM = 1    # Search term surrounded by quotes
    UNQUOTED_TERM = 2  # Array of unquoted terms
    AND = 3            # AND in all capital letters for binary and
    OR = 4             # OR in all capital letters for binary or
    NOT = 5            # NOT in all capital letters for unary not
    PAREN_L = 6        # (
    PAREN_R = 7        # )


def tokenize_query(query):
    '''
    Tokenizes a search query into an array of tokens for the parser to parse

     input: query - The query to tokenize
    output: the list of tokens
    '''

    # Evaluate the query length as is constantly referred to throughout
    # the tokenizer, and len(query) is O(N) :|
    query_length = len(query)

    token_stream = []

    # Index into the query
    i = 0

    # I have yet to be able to write an O(N) tokenizer that doesn't turn into a bunch of confusing control
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

    token_stream.append((TokenType.END,))

    return token_stream

if __name__ == "__main__":
    print(tokenize_query("(\'Hello\') OR NOT Bye Hello"))
