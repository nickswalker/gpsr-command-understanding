import operator

from gpsr_semantic_parser.tokens import WildCard, NonTerminal


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