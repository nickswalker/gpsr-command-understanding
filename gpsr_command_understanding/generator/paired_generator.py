import copy
import sys
from itertools import zip_longest

import importlib_resources
from lark import Lark, exceptions, Tree, Token

from gpsr_command_understanding.generator.generator import Generator
from gpsr_command_understanding.generator.grammar import RemovePrefix, TypeConverter, CompactUnderscorePrefixed, \
    tree_printer, expand_shorthand, DiscardVoid, CombineExpressions, NonTerminal
from gpsr_command_understanding.generator.tokens import ROOT_SYMBOL, WildCard
from gpsr_command_understanding.util import get_wildcards_forest, get_placeholders, has_nonterminals, \
    replace_child_in_tree

try:
    from queue import Queue as queue
except ImportError:
    from Queue import queue

SEMANTIC_FORMS = {"lambda": importlib_resources.read_text("gpsr_command_understanding.resources", "lambda_ebnf.lark")}


class LambdaParserWrapper:
    def __init__(self, grammar_spec=SEMANTIC_FORMS["lambda"]):
        # FIXME: Ensure that the import statement will work in different contexts
        # This grammar uses an import statement, which will trigger a local search for the imported file.
        # We aren't guaranteed that resources live as files (could be zipped up), so this will
        # probably break for distribution.
        with importlib_resources.path("gpsr_command_understanding.resources", "generator.lark") as path:
            # When a grammar comes in as a string, lark will check where the main script is located
            # to start its search. We'll manually point it to a path that importlib tells us has
            # the imported grammar.
            old_main = sys.modules['__main__'].__file__
            sys.modules['__main__'].__file__ = path
            self.parser = Lark(grammar_spec,
                               start='start', parser="lalr")
            # Because the imported rules come into a namespace, we'll have to run our own clean up, but then
            # it's as though we cut and pasted the imported rules
            self.post_process = RemovePrefix("generator__")
            self.compact = TypeConverter() * CompactUnderscorePrefixed()
            # Clean up
            sys.modules['__main__'].__file__ = old_main

    def parse(self, to_parse):
        parsed = self.parser.parse(to_parse)
        de_namespaced = self.post_process.visit(parsed)
        compacted_and_typed = self.compact.transform(de_namespaced)
        return compacted_and_typed


class PairedGenerator(Generator):
    def __init__(self, knowledge_base, grammar_format_version=2018, semantic_form_version="lambda"):
        super(PairedGenerator, self).__init__(knowledge_base, grammar_format_version=grammar_format_version)
        self.lambda_parser = LambdaParserWrapper()
        self.semantic_form_version = semantic_form_version
        self.semantics = {}

    @staticmethod
    def from_generator(plain_generator, **kwargs):
        paired = PairedGenerator(plain_generator.knowledge_base, plain_generator._grammar_format_version, **kwargs)
        paired.rules = plain_generator.rules
        return paired

    def __parse_rule(self, line, rule_dict):
        # Probably a comment line
        if "=" not in line:
            return 0
        # TODO: Properly compose these grammars so that we don't have to manually interface them
        prod, semantics = line.split("=")
        try:
            prod = self.sequence_parser.parse(prod.strip())
        except exceptions.LarkError as e:
            print(prod)
            print(e)
            raise e

        # Probably a comment
        if len(prod.children) == 0:
            return 0

        expanded_prod_heads = expand_shorthand(prod)
        sem = semantics.strip()

        try:
            sem = self.lambda_parser.parse(sem)
        except exceptions.LarkError as e:
            print(sem)
            print(e)
            raise e

        i = 0
        expanded_sem_heads = expand_shorthand(sem)
        for prod, sem in zip_longest(expanded_prod_heads, expanded_sem_heads, fillvalue=expanded_sem_heads[0]):
            # Check for any obvious errors in the annotation
            prod_wildcards = get_wildcards_forest([prod])
            sem_wildcards = get_wildcards_forest([sem]) if isinstance(sem, Tree) else set()

            if sem_wildcards.difference(prod_wildcards):
                raise RuntimeError(
                    "Semantics rely on non-terminal {} that doesn't occur in rule: {}".format(sem_wildcards, line))

            rule_dict[prod] = sem
            i += 1
        return i

    def load_semantics_rules(self, semantics_files):
        """
        :param semantics_files:
        :return: dictionary mapping productions in grammar to semantics for planner
        """

        if not isinstance(semantics_files, list):
            semantics_files = [semantics_files]
        i = 0
        for semantics_file in semantics_files:
            for line in semantics_file:
                cleaned = line.strip()
                i += self.__parse_rule(cleaned, self.semantics)

        return i

    def generate(self, start_pair, yield_requires_semantics=True,  # noqa: C901
                 branch_cap=None, random_generator=None):
        """
        Expand the start_symbols in breadth first order. At each expansion, see if we have an associated semantic template.
        If the current expansion has a semantics associated, also apply the expansion to the semantics.
        This is an efficient method of pairing the two grammars, but it only covers annotations that are carefully
        constructed to keep their head rule in the list of breadth first expansions of the utterance grammar.
        :param start_pair: the pair of sentence and semantics to have expansions applied to
        :param branch_cap: if there are too many expansions, set a fixed cap which will be applied
        :param random_generator: random number generator used to determine expansions, shuffling
        :param yield_requires_semantics: if true, will yield sentences that don't have associated semantics. Helpful for debugging.
        """

        # Make sure the start point is a Tree
        if isinstance(start_pair, NonTerminal):
            start_pair = (Tree("expression", [start_pair]), None)
        elif isinstance(start_pair, list):
            start_pair = (Tree("expression", start_pair), None)
        elif isinstance(start_pair, Tree):
            start_pair = (start_pair, None)
        else:
            assert isinstance(start_pair, tuple) and isinstance(start_pair[0], Tree)

        frontier = queue()
        frontier.put(start_pair)
        while not frontier.empty():
            sentence, semantics = frontier.get()
            if not semantics:
                # Let's see if the  expansion is associated with any semantics
                semantics = self.semantics.get(sentence)
            expansions = list(self.expand_pair(sentence, semantics, branch_cap=branch_cap,
                                               random_generator=random_generator))
            if not expansions:
                assert not has_nonterminals(sentence)
                # If we couldn't replace anything else, this sentence is done!
                if semantics:
                    DiscardVoid().visit(semantics)
                    CombineExpressions().visit(semantics)
                    sem_placeholders_remaining = get_placeholders(semantics)
                    sentence_placeholders_remaining = get_placeholders(sentence)
                    # If we have unexpanded non-terminals, something is wrong with the rules
                    assert not has_nonterminals(semantics)
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
                        quiet = False
                        # If the semantics are unknown, we probably meant to discard those wildcards
                        if semantics.children[0] == "UNKNOWN":
                            quiet = True
                        not_in_annotation = sentence_placeholders_remaining.difference(sem_placeholders_remaining)
                        # Pronouns don't appear in annotations, so we meant to throw that away
                        if len(not_in_annotation) == 1 and WildCard("pron") in not_in_annotation:
                            quiet = True
                        if not quiet:
                            print(
                                "Annotation is missing wildcards that are present in the original sentence. Were they left out accidentally?")
                            print(" ".join(map(str, not_in_annotation)))
                            print(tree_printer.transform(sentence))
                            print(tree_printer.transform(semantics))
                            print("")
                elif yield_requires_semantics:
                    # This won't be a pair without semantics, so we'll just skip it
                    continue
                yield sentence, semantics
                continue
            for pair in expansions:
                frontier.put(pair)

            # What productions don't have semantics?
            """if not modified_semantics:
                print(sentence_filled.pretty())
            """

    def expand_pair_full(self, sentence, semantics, branch_cap=None, random_generator=None):
        return self.generate(sentence, {}, start_semantics=semantics,
                             branch_cap=branch_cap, random_generator=random_generator)

    def expand_pair(self, sentence, semantics, branch_cap=None, random_generator=None):
        replace_tokens = list(sentence.scan_values(lambda x: x in self.rules.keys()))

        if not replace_tokens:
            return

        if random_generator:
            replace_token = random_generator.choice(replace_tokens)
            productions = self.rules[replace_token]
            if branch_cap:
                productions = random_generator.sample(productions, k=min(branch_cap, len(productions)))
            else:
                # Use all of the branches
                productions = self.rules[replace_token]
                random_generator.shuffle(productions)
        else:
            # We know we have at least one, so we'll just use the first
            replace_token = replace_tokens[0]
            productions = self.rules[replace_token]
            if branch_cap:
                productions = productions[:min(branch_cap, len(productions))]

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
                # NOTE: Produce needs to be a properly specified tree for the semantics to come out properly
                # Especially important if the rule expands to string. This needs to be a single
                # Token("ESCAPED_STRING",...)
                replace_child_in_tree(modified_semantics, replace_token, production)
            yield sentence_filled, modified_semantics

    def expand_all_semantics(self):
        """
        Expands all semantics rules
        """
        for utterance, parse in self.semantics.items():
            yield from self.generate(utterance, False)

    def generate_groundings(self, pair, random_generator=None, ignore_types=False):
        utt, logical = pair
        assignments = self.generate_grounding_assignments(utt, random_generator=random_generator,
                                                          ignore_types=ignore_types)
        for assignment in assignments:
            grounded_utt = copy.deepcopy(utt)
            grounded_logical = copy.deepcopy(logical)
            for token, replacement in assignment.items():
                replace_child_in_tree(grounded_utt, token, replacement)
                # We may not have had semantics
                if grounded_logical:
                    replace_child_in_tree(grounded_logical, token, Token("ESCAPED_STRING", "\"" + replacement + "\""))
            yield grounded_utt, grounded_logical

    def _print_semantics_rules(self):
        for key, expansion in self.semantics.items():
            print(tree_printer(key))
            print(tree_printer(expansion))
            print("----------------")


def pairs_without_placeholders(generator, only_in_grammar=False):
    pairs = generator.expand_all_semantics()
    out = {}
    if only_in_grammar:
        all_utterances_in_grammar = set(generator.generate(ROOT_SYMBOL, generator))
    for command, parse in pairs:
        if has_nonterminals(command) or has_nonterminals(parse):
            # This case is almost certainly a bug with the annotations
            print("Skipping pair for {} because it still has placeholders after expansion".format(
                command))
            continue
        # If it's important that we only get pairs that are in the grammar, check to make sure
        if only_in_grammar and command not in all_utterances_in_grammar:
            continue
        out[command] = parse
    return out
