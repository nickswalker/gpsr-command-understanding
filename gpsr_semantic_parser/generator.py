import os

from lark import Lark, Tree

from gpsr_semantic_parser.grammar import TypeConverter, expand_shorthand
from gpsr_semantic_parser.util import get_wildcards

GENERATOR_GRAMMARS={2018:(os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2018/generator_grammar_ebnf.txt"), os.path.abspath(os.path.dirname(__file__) + "/../resources/lambda_ebnf.txt")),
                    2019:(os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2019/generator_grammar_ebnf.txt"), os.path.abspath(os.path.dirname(__file__) + "/../resources/lambda_ebnf.txt"))}

class Generator:
    def __init__(self, grammar_format_version=2018):
        with  open(GENERATOR_GRAMMARS[grammar_format_version][0]) as grammar_spec, open(GENERATOR_GRAMMARS[grammar_format_version][1]) as annotation_spec:
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
        sem_wildcards = get_wildcards([sem]) if isinstance(sem, Tree) else set()
        for head in expanded_prod_heads:
            # Check for any obvious errors in the annotation
            head_wildcards = get_wildcards([head])
            if sem_wildcards.difference(head_wildcards):
                raise RuntimeError(
                    "Semantics rely on non-terminal {} that doesn't occur in rule: {}".format(sem_wildcards, line))

            rule_dict[head] = sem

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
                    self.parse_rule(cleaned, prod_to_semantics)

        return prod_to_semantics