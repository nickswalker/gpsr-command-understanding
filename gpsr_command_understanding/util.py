from collections import defaultdict

from more_itertools import peekable

from gpsr_command_understanding.generator.tokens import WildCard, NonTerminal


def merge_dicts(x, y):
    z = x.copy()  # start with x's keys and values
    z.update(y)  # modifies z with y's keys and values & returns None
    return z


def has_placeholders(tree):
    return any(tree.scan_values(lambda x: isinstance(x, WildCard) or isinstance(x, NonTerminal)))


def has_nonterminals(tree):
    return any(tree.scan_values(lambda x: isinstance(x, NonTerminal) and not isinstance(x, WildCard)))


def get_placeholders(tree):
    return set(tree.scan_values(lambda x: isinstance(x, WildCard) or isinstance(x, NonTerminal)))


def replace_child(tree, child_target, replacement, only_once=False):
    replace_count = 0
    for i, child in enumerate(tree.children):
        if child == child_target:
            tree.children[i] = replacement
            replace_count += 1
            if only_once and replace_count >= 1:
                return replace_count
    return replace_count


def replace_child_in_tree(tree, child_target, replacement, only_once=False):
    replace_count = 0
    for tree in tree.iter_subtrees():
        replace_count += replace_child(tree, child_target, replacement, only_once=only_once)
        if only_once and replace_count >= 1:
            return replace_count
    return replace_count


def get_wildcards(tree):
    return peekable(tree.scan_values(lambda x: isinstance(x, WildCard)))


def get_wildcards_forest(trees):
    """
    Get all wildcards that occur in a grammar
    :param production_rules:
    :return:
    """
    wildcards = set()
    for tree in trees:
        extracted = tree.scan_values(lambda x: isinstance(x, WildCard))
        for item in extracted:
            wildcards.add(item)
    return wildcards


def determine_unique_data(pairs):
    unique_utterance_pair = {}
    unique_parse_pair = defaultdict(list)

    for utterance, parse in pairs.items():
        unique_utterance_pair[utterance] = parse
        unique_parse_pair[parse].append(utterance)

    return unique_utterance_pair, unique_parse_pair


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def save_data(data, out_path):
    if len(data) == 0:
        print("Set is empty, not saving file")
        return
    data = sorted(data, key=lambda x: len(x[0]))
    with open(out_path, "w") as f:
        for sentence, parse in data:
            f.write(sentence + '\n' + str(parse) + '\n')


def flatten(original):
    flattened = []
    for parse, utterances in original:
        for utterance in utterances:
            flattened.append((utterance, parse))
    return flattened


def to_num(s):
    try:
        return int(s)
    except ValueError:
        return None


class ParseForward:
    def __init__(self, parser, start):
        self.__parser = parser
        self.__start = start

    def parse(self, string):
        return self.__parser.parse(string, self.__start)
