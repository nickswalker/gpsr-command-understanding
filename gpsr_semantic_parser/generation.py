import copy

from gpsr_semantic_parser.util import combine_adjacent_text_fragments
from gpsr_semantic_parser.types import NonTerminal, TextFragment
from Queue import Queue


def generate_sentences(start_symbols, production_rules):
    """
    A generator that produces completely expanded sentences in depth-first order
    :param start_symbols: the list of tokens to begin expanding
    :param production_rules: the rules to use for expanding the tokens
    """
    stack = [start_symbols]
    if not isinstance(start_symbols, list):
        stack = [[start_symbols]]

    while len(stack) != 0:
        tokens = stack.pop()
        replace_i, replace_token = None, None
        # Figure out the index of the next token to replace
        for i, token in enumerate(tokens):
            replace_i, replace_token = None, None
            if not isinstance(token, NonTerminal) or token not in production_rules.keys():
                continue
            replace_i, replace_token = i, token
            break

        if replace_token is not None:
            # Replace it every way we know how
            for production in production_rules[replace_token]:
                sentence_filled = tokens[:replace_i] + production + tokens[replace_i + 1:]
                # Generate the rest of the sentence recursively assuming this replacement
                stack.append(sentence_filled)
        else:
            # If we couldn't replace anything else, this sentence is done!
            tokens = combine_adjacent_text_fragments(tokens)
            yield tokens


def generate_sentence_parse_pairs(start_symbols, production_rules, semantics_rules, yield_requires_semantics=True):
    """
    Expand the start_symbols in breadth first order. At each expansion, see if we have an associated semantic template.
    If the current expansion has a semantics associated, also apply the expansion to the semantics.
    :param start_symbols:
    :param production_rules:
    :param semantics_rules: dict mapping a sequence of tokens to a semantic template
    :param yield_requires_semantics: if true, will yield sentences that don't have associated semantics. Helpful for debugging.
    """
    source = start_symbols
    if not isinstance(start_symbols, list):
        source = [start_symbols]
    replace_i, replace_token = None, None
    frontier = Queue()
    frontier.put((source, None))
    while not frontier.empty():
        tokens, semantics = frontier.get()
        for i, token in enumerate(tokens):
            replace_i, replace_token = None, None
            if not isinstance(token, NonTerminal) and token not in production_rules.keys():
                continue
            replace_i, replace_token = i, token
            break

        if not replace_token:
            # If we couldn't replace anything else, this sentence is done!
            tokens = combine_adjacent_text_fragments(tokens)
            if semantics:
                # We should've hit all the replacements. If not, there was probably a formatting issue with the template
                if len(semantics.unfilled_template_names) != 0:
                    print semantics.unfilled_template_names
                    assert False
            elif yield_requires_semantics:
                # This won't be a pair without semantics, so we'll just skip it
                continue
            yield (tokens, semantics)
            continue

        for production in production_rules[replace_token]:
            sentence_filled = tokens[:replace_i] + production + tokens[replace_i + 1:]
            # Normalize any chopped up text fragments to make sure we can pull semantics for these cases
            sentence_filled = combine_adjacent_text_fragments(sentence_filled)
            # If we've got semantics for this expansion already, see if the replacements apply to them
            # For the basic annotation we provided, this should only happen when expanding ground terms
            modified_semantics = None
            if semantics:
                if replace_token.name in semantics.unfilled_template_names:
                    modified_semantics = copy.deepcopy(semantics)
                    modified_semantics.fill_template(replace_token.name, production[0])
                else:
                    modified_semantics = semantics
            else:
                # Let's see if the  expansion is associated with any semantics
                modified_semantics = semantics_rules.get(tuple(sentence_filled))
            frontier.put((sentence_filled, modified_semantics))

