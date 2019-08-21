import itertools
from collections import defaultdict

from gpsr_command_understanding.tokens import WildCard, NonTerminal
from lark import Token


def merge_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z


def has_placeholders(tree):
    return any(tree.scan_values(lambda x: isinstance(x, WildCard) or isinstance(x, NonTerminal)))


def get_placeholders(tree):
    return set(tree.scan_values(lambda x: isinstance(x, WildCard) or isinstance(x, NonTerminal)))


def replace_child(tree, child_target, replacement, only_once=False):
    did_replace = False
    for i, child in enumerate(tree.children):
        if child == child_target:
            tree.children[i] = replacement
            did_replace = True
            if only_once and did_replace:
                return did_replace
    return did_replace


def replace_child_in_tree(tree, child_target, replacement, only_once=False):
    did_replace = False
    for tree in tree.iter_subtrees():
        did_replace = replace_child(tree, child_target, replacement, only_once=only_once)
        if only_once and did_replace:
            return did_replace
    return did_replace


def replace_words_in_tree(tree, replacement):
    for tree in tree.iter_subtrees():
        for i, child in enumerate(tree.children):
            if (isinstance(child, Token) and child.type == 'WORD') or (type(child) is str):
                tree.children[i] = replacement


def replace_slots_in_tree(tree, slot):
    first = True
    for tree in tree.iter_subtrees():
        for i, child in enumerate(tree.children):
            if (isinstance(child, Token) and child.type == 'WORD') or (type(child) is str):
                if first:
                    tree.children[i] = "B-" + slot
                    first = False
                else:
                    tree.children[i] = "I-" + slot


def get_wildcards(trees):
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


def determine_unique_cat_data(cat_data, keep_new_utterance_repeat_parse_for_lower_cat=True):
    unique_utterance_pair = []
    unique_parse_pair = []

    for i, cat_pairs in enumerate(cat_data):
        cat_unique_utterance_pair = {}
        cat_unique_parse_pair = defaultdict(list)

        for utterance, parse in cat_pairs.items():
            utterance_unique_to_cat = True
            parse_unique_to_cat = True
            for j, (prev_cat_by_utt, prev_cat_by_parse) in enumerate(zip(unique_utterance_pair[:i], unique_parse_pair[:i])):

                # If this utterance was in a prev cat, then we know that neither the utterance
                # nor the parse are unique (because utterances always produce a unique parse)
                if utterance in prev_cat_by_utt.keys():
                    utterance_unique_to_cat = False
                    parse_unique_to_cat = False
                    break

                # Even if the utterance is unique, its parse might not be.
                if parse in prev_cat_by_parse.keys():
                    parse_unique_to_cat = False
                    # In that case, we can take the parse to "belong to the previous category", and tack
                    # on this utterance as training data in category 1
                    if keep_new_utterance_repeat_parse_for_lower_cat:
                        prev_cat_by_parse[parse].append(utterance)

            if utterance_unique_to_cat:
                cat_unique_utterance_pair[utterance] = parse
            if parse_unique_to_cat:
                cat_unique_parse_pair[parse].append(utterance)
        unique_utterance_pair.append(cat_unique_utterance_pair)
        unique_parse_pair.append(cat_unique_parse_pair)
    return unique_utterance_pair, unique_parse_pair


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def save_data(data, out_path):
    if len(data)== 0:
        print("Set is empty, not saving file")
        return
    data = sorted(data, key=lambda x: len(x[0]))
    with open(out_path, "w") as f:
        for sentence, parse in data:
            f.write(sentence + '\n' + str(parse) + '\n')


def save_slot_data(data, out_path):
    data = sorted(data, key=lambda x: len(x[0]))
    with open(out_path, "w") as f:
        for sentence, parse in data:
            sentence_tokens = sentence.split(" ")
            parse_tokens = parse.split(" ")
            width = max(len(x) for x in itertools.chain(sentence_tokens, parse_tokens))
            sentence_str = " ".ljust(width+1) + " ".join(token.ljust(width) for token in sentence_tokens)
            f.write(sentence_str + "\n")
            f.write(" ".join(token.ljust(width) for token in parse_tokens) + "\n")
            #print(sentence_str)
            #print(" ".join(token.ljust(width) for token in parse_tokens))


def flatten(original):
    flattened = []
    for parse, utterances in original:
        for utterance in utterances:
            flattened.append((utterance, parse))
    return flattened


def get_pairs_by_cats(data, train_categories, test_categories):
    train_pairs = []
    for cat in train_categories:
        # Cats are 1 indexed. Subtract to get 0 indexed
        for pair in data[cat - 1].items():
            train_pairs.append(pair)

    test_pairs = []
    for cat in test_categories:
        # Cats are 1 indexed. Subtract to get 0 indexed
        for pair in data[cat - 1].items():
            test_pairs.append(pair)

    return train_pairs, test_pairs


def to_num(s):
    try:
        return int(s)
    except ValueError:
        return None
