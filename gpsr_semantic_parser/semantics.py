import os

from lark import Lark, Tree

from gpsr_semantic_parser.grammar import generator_grammar_parser, expand_shorthand, TypeConverter
from gpsr_semantic_parser.util import get_wildcards

lambda_parser = Lark(open(os.path.abspath(os.path.dirname(__file__) + "/../resources/lambda_ebnf.txt")), start='start', parser="lalr", transformer=TypeConverter())


def parse_rule(line, rule_dict):
    prod, semantics = line.split("=")
    prod = generator_grammar_parser.parse(prod.strip())
    expanded_prod_heads = expand_shorthand(prod)
    sem = semantics.strip()
    sem = lambda_parser.parse(sem)
    sem_wildcards = get_wildcards([sem]) if isinstance(sem, Tree) else set()
    for head in expanded_prod_heads:
        # Check for any obvious errors in the annotation
        head_wildcards = get_wildcards([head])
        if sem_wildcards.difference(head_wildcards):
            raise RuntimeError("Semantics rely on non-terminal {} that doesn't occur in rule: {}".format(sem_wildcards, line))

        rule_dict[head] = sem


def load_semantics(semantics_file_paths):
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
                parse_rule(cleaned, prod_to_semantics)

    return prod_to_semantics