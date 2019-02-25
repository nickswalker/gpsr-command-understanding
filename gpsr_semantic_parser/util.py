from gpsr_semantic_parser.types import TextFragment
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