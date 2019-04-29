import os

from lark import Lark, Tree

from gpsr_semantic_parser.generation import generate_sentence_parse_pairs, generate_sentence_slot_pairs, expand_pair_full
from gpsr_semantic_parser.grammar import TypeConverter, expand_shorthand
from gpsr_semantic_parser.util import get_wildcards, has_placeholders
from gpsr_semantic_parser.tokens import NonTerminal, WildCard, Anonymized, ROOT_SYMBOL
from gpsr_semantic_parser.grammar import tree_printer

from itertools import zip_longest

GENERATOR_GRAMMARS={2018: os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2018/generator_grammar_ebnf.txt"),
                    2019: os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2019/generator_grammar_ebnf.txt")}

SEMANTIC_FORMS={"lambda": os.path.abspath(os.path.dirname(__file__) + "/../resources/lambda_ebnf.txt"),
                "slot": os.path.abspath(os.path.dirname(__file__) + "/../resources/slot_ebnf.txt")}

class Generator:
    def __init__(self, grammar_format_version=2018, semantic_form_version="lambda"):
        with  open(GENERATOR_GRAMMARS[grammar_format_version]) as grammar_spec, open(SEMANTIC_FORMS[semantic_form_version]) as annotation_spec:
            self.generator_grammar_parser = Lark(grammar_spec,
            start='start', parser="lalr", transformer=TypeConverter())
            self.lambda_parser = Lark(annotation_spec,
                             start='start', parser="lalr", transformer=TypeConverter())


    def parse_production_rule(self, line):
        #print(line)
        parsed = self.generator_grammar_parser.parse(line)
        rhs_list_expanded = expand_shorthand(parsed.children[1])
        #print(parsed.pretty())
        return parsed.children[0], rhs_list_expanded


    def load_rules(self, grammar_file_paths):
        """
        :param grammar_file_paths: list of file paths
        :return: dictionary with NonTerminal key and values for all productions
        """
        if isinstance(grammar_file_paths, str):
            grammar_file_paths = [grammar_file_paths]
        production_rules = {}
        for grammar_file_path in grammar_file_paths:
            with open(grammar_file_path) as f:
                for line in f:
                    line = line.strip()
                    # TODO: Rely on the grammar to ignore comments instead..
                    if len(line) == 0 or line[0] != '$':
                        # We only care about lines that start with a nonterminal (denoted by $)
                        continue
                    # parse into possible productions
                    lhs, rhs_productions = self.parse_production_rule(line)
                    # add to dictionary, if already there then append to list of rules
                    # using set to avoid duplicates
                    if lhs not in production_rules:
                        production_rules[lhs] = rhs_productions
                    else:
                        production_rules[lhs].extend(rhs_productions)
        return production_rules

    def parse_rule(self, line, rule_dict):
        prod, semantics = line.split("=")
        prod = self.generator_grammar_parser.parse(prod.strip())
        expanded_prod_heads = expand_shorthand(prod)
        sem = semantics.strip()
        sem = self.lambda_parser.parse(sem)
        expanded_sem_heads = expand_shorthand(sem)
        for prod, sem in zip_longest(expanded_prod_heads, expanded_sem_heads, fillvalue=expanded_sem_heads[0]):
            # Check for any obvious errors in the annotation
            prod_wildcards = get_wildcards([prod])
            sem_wildcards = get_wildcards([sem]) if isinstance(sem, Tree) else set()
            if sem_wildcards.difference(prod_wildcards):
                raise RuntimeError(
                    "Semantics rely on non-terminal {} that doesn't occur in rule: {}".format(sem_wildcards, line))

            rule_dict[prod] = sem

    def load_semantics_rules(self, semantics_file_paths):
        """
        :param semantics_file_paths:
        :return: dictionary mapping productions in grammar to semantics for planner
        """

        if isinstance(semantics_file_paths, str):
            semantics_file_paths = [semantics_file_paths]
        prod_to_semantics = {}
        for semantics_file_path in semantics_file_paths:
            with open(semantics_file_path) as f:
                for line in f:
                    cleaned = line.strip()
                    if len(cleaned) == 0 or cleaned[0] == '#':
                        continue
                    #print(cleaned)
                    self.parse_rule(cleaned, prod_to_semantics)

        return prod_to_semantics


def get_grounding_per_each_parse(generator, random_source):
    grounded_examples = {}

    for rules, rules_anon, rules_ground, semantics in generator:
        # Start with each rule, since this is guaranteed to get at least all possible parses
        # Note, this may include parses that don't fall in the grammar...
        for generation_path, semantic_production in semantics.items():
            # Some non-terminals may expand into different parses (like $oprop)! So we'll expand them
            # every which way
            wild_expansions = list(generate_sentence_parse_pairs(generation_path, rules, semantics,
                                                            yield_requires_semantics=True,
                                                            generator=random_source))
            # We're going to be throwing away expansions that have the same parse, so let's
            # randomize here to make sure we aren't favoring the last expansion.
            # Note that the above generation should also return expansions in a random order anyway
            random_source.shuffle(wild_expansions)

            for utterance_wild, parse_wild in list(wild_expansions):
                utterance_anon, parse_anon = next(expand_pair_full(utterance_wild, parse_wild, rules_anon, branch_cap=1,
                                                              generator=random_source))

                utterance, parse_ground = next(expand_pair_full(utterance_wild, parse_wild, rules_ground, branch_cap=1,
                                                                generator=random_source))
                assert not has_placeholders(utterance)
                assert not has_placeholders(parse_ground)
                assert not has_placeholders(parse_ground)
                # We expect this to happen sometimes because of the cat1 cat2 object known wildcard situation
                if has_placeholders(parse_anon):
                    continue

                grounded_examples[parse_anon] = (utterance, parse_anon, parse_ground)

    return list(grounded_examples.values())


def get_grounding_per_each_parse_by_cat(generator, random_source):
    grounded_examples = []

    for rules, rules_anon, rules_ground, semantics in generator:
        cat_groundings = {}
        # Start with each rule, since this is guaranteed to get at least all possible parses
        # Note, this may include parses that don't fall in the grammar...
        for generation_path, semantic_production in semantics.items():
            # Some non-terminals may expand into different parses (like $oprop)! So we'll expand them
            # every which way
            wild_expansions = list(generate_sentence_parse_pairs(generation_path, rules, semantics,
                                                            yield_requires_semantics=True,
                                                            generator=random_source))
            # We're going to be throwing away expansions that have the same parse, so let's
            # randomize here to make sure we aren't favoring the last expansion.
            # Note that the above generation should also return expansions in a random order anyway
            random_source.shuffle(wild_expansions)

            for utterance_wild, parse_wild in list(wild_expansions):
                utterance_anon, parse_anon = next(expand_pair_full(utterance_wild, parse_wild, rules_anon, branch_cap=1,
                                                              generator=random_source))

                utterance, parse_ground = next(expand_pair_full(utterance_wild, parse_wild, rules_ground, branch_cap=1,
                                                                generator=random_source))
                assert not has_placeholders(utterance)
                assert not has_placeholders(parse_ground)
                assert not has_placeholders(parse_ground)
                # We expect this to happen sometimes because of the cat1 cat2 object known wildcard situation
                if has_placeholders(parse_anon):
                    continue

                cat_groundings[parse_anon] = (utterance, parse_anon, parse_ground)
        grounded_examples.append(list(cat_groundings.values()))
    return grounded_examples

def get_utterance_slot_pairs(generator, random_source):
    grounded_examples = []


    for rules, rules_anon, rules_ground, semantics in generator:
        cat_groundings = {}

        pairs = generate_sentence_slot_pairs(ROOT_SYMBOL, rules_ground, semantics, 
                                        yield_requires_semantics=True,
                                        branch_cap=1,
                                        random_generator=random_source)
        for sentence, semantics in pairs:
            print(tree_printer(sentence))
            print(tree_printer(semantics))
        #for generation_path, semantic_production in semantics.items():
        #    print (generation_path)
        #    print (semantic_production)