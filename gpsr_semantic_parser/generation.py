import copy

from lark import Tree

from gpsr_semantic_parser.grammar import CombineExpressions, tree_printer, DiscardVoid
from gpsr_semantic_parser.util import get_placeholders, replace_child_in_tree, has_placeholders
from gpsr_semantic_parser.tokens import NonTerminal, WildCard, Anonymized, ROOT_SYMBOL
from queue import Queue


def generate_sentences(start_tree, production_rules):
    """
    A generator that produces completely expanded sentences in depth-first order
    :param start_tree: the list of tokens to begin expanding
    :param production_rules: the rules to use for expanding the tokens
    """
    # Make sure the start point is a Tree
    if isinstance(start_tree, NonTerminal):
        stack = [Tree("expression", [start_tree])]
    elif isinstance(start_tree, list):
        stack = [Tree("expression", start_tree)]
    else:
        stack = [start_tree]

    while len(stack) != 0:
        sentence = stack.pop()
        replace_tokens = list(sentence.scan_values(lambda x: x in production_rules.keys()))
        if replace_tokens:
            replace_token = replace_tokens[0]
            # Replace it every way we know how
            for production in production_rules[replace_token]:
                modified_sentence = copy.deepcopy(sentence)
                replace_child_in_tree(modified_sentence, replace_token, production, only_once=True)
                # Generate the rest of the sentence recursively assuming this replacement
                stack.append(modified_sentence)
        else:
            # If we couldn't replace anything else, this sentence is done!
            sentence = CombineExpressions().visit(sentence)
            sentence = DiscardVoid().visit(sentence)
            yield sentence


def generate_random_pair(start_symbols, production_rules, semantics_rules, yield_requires_semantics=False, generator=None):
    return next(generate_sentence_parse_pairs(start_symbols, production_rules, semantics_rules, yield_requires_semantics=yield_requires_semantics, branch_cap=1, generator=generator))


def generate_sentence_parse_pairs(start_tree, production_rules, semantics_rules, start_semantics=None, yield_requires_semantics=True, branch_cap=None, generator=None):
    """
    Expand the start_symbols in breadth first order. At each expansion, see if we have an associated semantic template.
    If the current expansion has a semantics associated, also apply the expansion to the semantics.
    This is an efficient method of pairing the two grammars, but it only covers annotations that are carefully
    constructed to keep their head rule in the list of breadth first expansions of the utterance grammar.
    :param start_tree:
    :param production_rules:
    :param semantics_rules: dict mapping a sequence of tokens to a semantic template
    :param yield_requires_semantics: if true, will yield sentences that don't have associated semantics. Helpful for debugging.
    """
    """print(parsed.pretty())
    to_str = ToString()
    result = to_str.transform(parsed)
    print(result)"""

    # Make sure the start point is a Tree
    if isinstance(start_tree, NonTerminal):
        start_tree = Tree("expression", [start_tree])
    elif isinstance(start_tree, list):
        start_tree = Tree("expression", start_tree)
    else:
        assert isinstance(start_tree, Tree)

    frontier = Queue()
    frontier.put((start_tree, start_semantics))
    while not frontier.empty():
        sentence, semantics = frontier.get()
        if not semantics:
            # Let's see if the  expansion is associated with any semantics
            semantics = semantics_rules.get(sentence)
        expansions = list(expand_pair(sentence, semantics, production_rules, branch_cap=branch_cap, generator=generator))
        if not expansions:
            # If we couldn't replace anything else, this sentence is done!
            if semantics:
                semantics = DiscardVoid().visit(semantics)
                sem_placeholders_remaining = get_placeholders(semantics)
                sentence_placeholders_remaining = get_placeholders(sentence)
                # Are there placeholders in the semantics that aren't left in the sentence? These will never get expanded,
                # so it's almost certainly an error
                probably_should_be_filled = sem_placeholders_remaining.difference(sentence_placeholders_remaining)
                if len(probably_should_be_filled) > 0:
                    print("Unfilled placeholders {}".format(" ".join(map(str, probably_should_be_filled))))
                    print(tree_printer.transform(sentence))
                    print(tree_printer.transform(semantics))
                    print("This annotation is probably wrong")
                    print("")
                    continue
                elif len(sem_placeholders_remaining) != len(sentence_placeholders_remaining):
                    not_in_annotation = sentence_placeholders_remaining.difference(sem_placeholders_remaining)
                    print("Annotation is missing wildcards that are present in the original sentence. Were they left out accidentally?")
                    print(" ".join(map(str,not_in_annotation)))
                    print(tree_printer.transform(sentence))
                    print(tree_printer.transform(semantics))
                    print("")
            elif yield_requires_semantics:
                # This won't be a pair without semantics, so we'll just skip it
                continue
            yield (sentence, semantics)
            continue
        for pair in expansions:
            frontier.put(pair)

        # What productions don't have semantics?
        """if not modified_semantics:
            print(sentence_filled.pretty())
        """


def expand_pair_full(sentence, semantics, production_rules, branch_cap=None, generator=None):
    return generate_sentence_parse_pairs(sentence, production_rules, {}, start_semantics=semantics,
                                       branch_cap=branch_cap, generator=generator)


def expand_pair(sentence, semantics, production_rules, branch_cap=None, generator=None):
        replace_token = list(sentence.scan_values(lambda x: x in production_rules.keys()))

        if not replace_token:
            return None

        if generator:
            replace_token = generator.choice(replace_token)
            replacement_rules = production_rules[replace_token]
            if branch_cap:
                productions = generator.sample(replacement_rules, k=branch_cap)
            else:
                # Use all of the branches
                productions = production_rules[replace_token]
                generator.shuffle(productions)
        else:
            # We know we have at least one, so we'll just use the first
            replace_token = replace_token[0]
            productions = production_rules[replace_token]

        for production in productions:
            modified_sentence = copy.deepcopy(sentence)
            replace_child_in_tree(modified_sentence, replace_token, production, only_once=True)
            modified_sentence = DiscardVoid().visit(modified_sentence)

            # Normalize any chopped up text fragments to make sure we can pull semantics for these cases
            sentence_filled = CombineExpressions().visit(modified_sentence)
            # If we've got semantics for this expansion already, see if the replacements apply to them
            # For the basic annotation we provided, this should only happen when expanding ground terms
            modified_semantics = None
            if semantics:
                modified_semantics = copy.deepcopy(semantics)
                sem_substitute = production
                if isinstance(replace_token, WildCard) or (len(production.children) >0 and isinstance(production.children[0], Anonymized)):
                    sem_substitute = production.copy()
                    sem_substitute.children = ["\""] + sem_substitute.children + ["\""]
                replace_child_in_tree(modified_semantics, replace_token, sem_substitute)
            yield sentence_filled, modified_semantics


def expand_all_semantics(production_rules, semantics_rules):
    """
    Expands all semantics rules
    :param production_rules:
    :param semantics_rules:
    """
#    for utterance, parse in [list(semantics_rules.items())[-1]]:
    for utterance, parse in semantics_rules.items():
        yield from generate_sentence_parse_pairs(utterance, production_rules, semantics_rules, False)
    return


def pairs_without_placeholders(rules, semantics, only_in_grammar=False):
    pairs = expand_all_semantics(rules, semantics)
    out = {}
    all_utterances_in_grammar = set(generate_sentences(ROOT_SYMBOL, rules))
    for utterance, parse in pairs:
        if has_placeholders(utterance) or has_placeholders(parse):
            # This case is almost certainly a bug with the annotations
            print("Skipping pair for {} because it still has placeholders after expansion".format(
                tree_printer(utterance)))
            continue
        # If it's important that we only get pairs that are in the grammar, check to make sure
        if only_in_grammar and not utterance in all_utterances_in_grammar:
            continue
        out[tree_printer(utterance)] = tree_printer(parse)
    return out