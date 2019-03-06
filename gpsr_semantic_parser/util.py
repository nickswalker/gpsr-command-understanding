from gpsr_semantic_parser.types import TextFragment, BAR, L_PAREN, R_PAREN
from types import *

def merge_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z

def tokens_to_text(tokens):
    output = ""
    for token in tokens:
        if isinstance(token, str):
            output += token + ' '
        else:
            output += token.to_human_readable() + ' '
    return output[:-1]


def remove_within_braces(keyword, line):
    # find meta in sentence and then count left  and right {} until we have more right than left
    start = line.find(keyword)
    left_brace_cnt = 0
    right_brace_cnt = 0
    indx = start
    while indx < len(line) - 1 and left_brace_cnt >= right_brace_cnt:
        indx += 1
        if line[indx] == "{":
            left_brace_cnt += 1
        elif line[indx] == "}":
            right_brace_cnt += 1
    # print "to remove:", line[start:indx]
    line = line.replace(line[start:indx], "")
    return line


def combine_adjacent_text_fragments(tokens):
    """
    Grammars may generate multiple text fragments in a sequence. This will combine them
    :param tokens:
    :return: a list of tokens with no adjacent text fragments
    """
    cleaned = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if not isinstance(token, TextFragment):
            cleaned.append(token)
            i += 1
            continue
        j = i + 1
        while j < len(tokens):
            next_token = tokens[j]
            if isinstance(next_token, TextFragment):
                j += 1
                continue
            break
        cleaned.append(TextFragment.join(tokens[i:j]))
        i = j
    if i == len(tokens) - 1:
        cleaned.append(tokens[i])
    return cleaned


def normalize(s):
    for p in ['?', '.', '.', ',', '!']:
        s = s.replace(p, '')

    return s.lower().strip()


def expand_shorthand(prefix_tokens, remaining_tokens, state, all_expansions):
    """
    The grammar allows a shorthand for specifying alternate productions
    This (is | will be | can be | should be) awesome ((someday | someday soon) | now)
    :param prefix_tokens:
    :param remaining_tokens:
    :param state:
    :param all_expansions:
    :return:
    """
    if len(remaining_tokens) == 0:
        all_expansions.append(prefix_tokens)
        return all_expansions
    for i, token in enumerate(remaining_tokens):
        if token == BAR:
            if state == "ALPH":
                all_expansions.append(prefix_tokens + remaining_tokens[0:i])
                return expand_shorthand(prefix_tokens, remaining_tokens[i + 1:], state, all_expansions)
            elif state == "PAREN_START":
                state_n = "PAREN_END"
                prefix_n = prefix_tokens + remaining_tokens[0:i]
                expand_shorthand(prefix_n, remaining_tokens[i + 1:], state_n, all_expansions)
                # start another branch for production B in (A | B | ...)
                return expand_shorthand(prefix_tokens, remaining_tokens[i + 1:], state, all_expansions)
            elif state == "PAREN_END":
                continue  # searching for )
        elif token == L_PAREN:
            state_n = "PAREN_START"
            prefix_n = prefix_tokens + remaining_tokens[0:i]
            return expand_shorthand(prefix_n, remaining_tokens[i + 1:], state_n, all_expansions)
        elif token == R_PAREN:
            if state == "PAREN_END":
                state = "ALPH"
                return expand_shorthand(prefix_tokens, remaining_tokens[i + 1:], state, all_expansions)
            elif state == "PAREN_START":
                state = "ALPH"
                prefix_n = prefix_tokens + remaining_tokens[0:i]
                return expand_shorthand(prefix_n, remaining_tokens[i + 1:], state, all_expansions)
    all_expansions.append(prefix_tokens + remaining_tokens)
    return all_expansions