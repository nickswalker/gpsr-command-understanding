import copy

from lark import Tree

from gpsr_semantic_parser.grammar import CombineExpressions, tree_printer, DiscardVoid
from gpsr_semantic_parser.util import get_placeholders, replace_child_in_tree
from gpsr_semantic_parser.tokens import NonTerminal
from queue import Queue
import random


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


def generate_sentence_parse_pairs(start_tree, production_rules, semantics_rules, yield_requires_semantics=True, branch_cap=-1, generator=None):
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

    semantics = semantics_rules.get(start_tree)
    frontier = Queue()
    frontier.put((start_tree, semantics))
    while not frontier.empty():
        sentence, semantics = frontier.get()
        replace_token = list(sentence.scan_values(lambda x: x in production_rules.keys()))
        if not replace_token:
            # If we couldn't replace anything else, this sentence is done!
            if semantics:
                semantics = DiscardVoid().visit(semantics)
                # We should've hit all the replacements. If not, there was probably a formatting issue with the template
                placeholders_remaining = get_placeholders(semantics)
                if len(placeholders_remaining) != 0:
                    print("Unfilled placeholders {} \nin template {}".format(" ".join(map(str, placeholders_remaining)), tree_printer.transform(semantics)))
                    print("Won't accept these semantics")
                    continue
            elif yield_requires_semantics:
                # This won't be a pair without semantics, so we'll just skip it
                continue
            yield (sentence, semantics)
            continue

        if generator:
            replace_token = generator.choice(replace_token)
            productions = random.choices(production_rules[replace_token],k=branch_cap)
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
                replace_child_in_tree(modified_semantics, replace_token, production)
            else:
                # Let's see if the  expansion is associated with any semantics
                modified_semantics = semantics_rules.get(sentence_filled)
            frontier.put((sentence_filled, modified_semantics))
            # What productions don't have semantics?
            """if not modified_semantics:
                print(sentence_filled.pretty())
            """


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

