import copy

from gpsr_semantic_parser.util import combine_adjacent_text_fragments, tokens_to_str, productions_to_str, Counter
from gpsr_semantic_parser.types import NonTerminal, TextFragment
from queue import Queue

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
    This is an efficient method of pairing the two grammars, but it only covers annotations that are carefully
    constructed to keep their head rule in the list of breadth first expansions of the utterance grammar.
    :param start_symbols:
    :param production_rules:
    :param semantics_rules: dict mapping a sequence of tokens to a semantic template
    :param yield_requires_semantics: if true, will yield sentences that don't have associated semantics. Helpful for debugging.
    """
    source = start_symbols
    if not isinstance(start_symbols, list):
        source = [start_symbols]
    semantics = semantics_rules.get(tuple(source))
    replace_i, replace_token = None, None
    frontier = Queue()
    frontier.put((source, semantics))
    while not frontier.empty():
        tokens, semantics = frontier.get()
        for i, token in enumerate(tokens):
            replace_i, replace_token = None, None
            if token not in production_rules.keys():
                continue
            replace_i, replace_token = i, token
            break

        if not replace_token:
            # If we couldn't replace anything else, this sentence is done!
            tokens = combine_adjacent_text_fragments(tokens)
            if semantics:
                # We should've hit all the replacements. If not, there was probably a formatting issue with the template
                if len(semantics.unfilled_template_names) != 0:
                    print("Unfilled placeholders {} \nin template {}".format(str(semantics.unfilled_template_names), str(semantics)))
                    print("Won't accept these semantics")
                    continue
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
                if str(replace_token) in semantics.unfilled_template_names:
                    modified_semantics = copy.deepcopy(semantics)
                    modified_semantics.fill_template(str(replace_token), production[0])
                else:
                    modified_semantics = semantics
            else:
                # Let's see if the  expansion is associated with any semantics
                modified_semantics = semantics_rules.get(tuple(sentence_filled))
            frontier.put((sentence_filled, modified_semantics))
            if not modified_semantics:
                print(tokens_to_str(sentence_filled))


def generate_sentence_parse_pairs_exhaustive(start_symbols, production_rules, semantics_rules, log_production_path=True):
    """
    Expand the start_symbols in _every possible ordering_ to ensure our annotations apply. Once we hit an annotation,
    we can expand the children in any order. This method is primarily useful for figuring out what annotations
    we're missing.
    :param start_symbols:
    :param production_rules:
    :param semantics_rules: dict mapping a sequence of tokens to a semantic template
    """
    source = start_symbols
    # Sometimes may want to pass a single symbol (like ROOT)
    if not isinstance(start_symbols, list):
        source = [start_symbols]
    semantics = semantics_rules.get(tuple(source))
    frontier = Queue()
    frontier.put((source, semantics, []))

    most_used_productions = Counter()
    most_used_semantics = Counter()
    for head, body in semantics_rules.items():
        most_used_semantics[tuple(head)] = 1
    while not frontier.empty():
        tokens, semantics, path = frontier.get()
        replaced = False
        for i, token in enumerate(tokens):
            if not isinstance(token, NonTerminal) and token not in production_rules.keys():
                continue
            replace_i, replace_token = i, token
            replaced = True
            for production in production_rules[replace_token]:
                new_path = []
                if log_production_path:
                    rule = (replace_token, tuple(production))
                    new_path = path + [rule]

                sentence_filled = tokens[:replace_i] + production + tokens[replace_i + 1:]
                # Normalize any chopped up text fragments to make sure we can pull semantics for these cases
                sentence_filled = combine_adjacent_text_fragments(sentence_filled)
                # If we've got semantics for this expansion already, see if the replacements apply to them
                # For the basic annotation we provided, this should only happen when expanding ground terms
                modified_semantics = None
                if semantics:
                    if str(replace_token) in semantics.unfilled_template_names:
                        modified_semantics = copy.deepcopy(semantics)
                        modified_semantics.fill_template(str(replace_token), production[0])
                        assert len(production) == 1
                    else:
                        modified_semantics = semantics
                else:
                    # Let's see if the expansion is associated with any semantics
                    modified_semantics = semantics_rules.get(tuple(sentence_filled))
                    if modified_semantics:
                        most_used_semantics[tuple(sentence_filled)] = 0
                        all_in_frontier = list(frontier.queue)
                        new_frontier = Queue()
                        for other_token, other_sem, other_path in all_in_frontier:
                            subset = True
                            # Check if every part in the current expansion's path is in the other path.
                            # If it is, that means that we'll handle it in the course of finishing this path's expansion.
                            for part in new_path:
                                if part not in other_path:
                                    subset = False
                                    break
                            if not subset:
                                new_frontier.put((other_token, other_sem, other_path))
                        #print(frontier.qsize(), new_frontier.qsize())
                        frontier = new_frontier

                frontier.put((sentence_filled, modified_semantics, new_path))

            if semantics:
                # Semantics attached to this branch means the ordering of all other expansions don't matter, so we're
                # fine just having done the leftmost expansion
                break

        if not replaced:
            # If we couldn't replace anything else, this sentence is done!
            tokens = combine_adjacent_text_fragments(tokens)
            if semantics:
                # We should've hit all the replacements. If not, there was probably a formatting issue with the template
                if len(semantics.unfilled_template_names) != 0:
                    message = "Did not expand {}\nTemplate: {}\nPath: {}\nFinal tokens: {}".format(semantics.unfilled_template_names, str(semantics), productions_to_str(path), tokens_to_str(tokens))
                    raise RuntimeError(message)
                yield (tokens, semantics)
            else:
                print("Productions that had no semantics:")
                for part in path:
                    most_used_productions[part] += 1
                most_used = most_used_productions.sortedKeys()
                for rule in most_used:
                    times_used = most_used_productions[rule]
                    print(productions_to_str([rule]) + '\t' + str(times_used))

                """print("semantics")
                most_used = most_used_semantics.sortedKeys()
                for rule in most_used:
                    print(tokens_to_str(rule), most_used_semantics[rule])
                print('\n')
                """
                print('\n')
                print("No semantics for: {}\nPath: {}".format(tokens_to_str(tokens),  productions_to_str(path)))
                print('-----')
                pass


def expand_all_semantics(production_rules, semantics_rules):
    """
    Expands all semantics rules
    :param production_rules:
    :param semantics_rules:
    """
#    for utterance, parse in [list(semantics_rules.items())[-1]]:
    for utterance, parse in semantics_rules.items():
        yield from generate_sentence_parse_pairs(list(utterance), production_rules, semantics_rules, False)
    return

