import os
from os.path import join

from gpsr_semantic_parser.grammar import prepare_rules, tree_printer
from gpsr_semantic_parser.tokens import ROOT_SYMBOL
from gpsr_semantic_parser.generation import generate_random_pair
from gpsr_semantic_parser.semantics import load_semantics
from gpsr_semantic_parser.util import assert_no_placeholders
import random

grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2018/")
common_path = join(grammar_dir, "common_rules.txt")

paths = tuple(map(lambda x: join(grammar_dir, x), ["objects.xml", "locations.xml", "names.xml", "gestures.xml"]))

cat1_rules = prepare_rules(common_path, join(grammar_dir, "gpsr_category_1_grammar.txt"), *paths)
cat2_rules = prepare_rules(common_path, join(grammar_dir, "gpsr_category_2_grammar.txt"), *paths)
cat3_rules = prepare_rules(common_path, join(grammar_dir, "gpsr_category_3_grammar.txt"), *paths)
cat1_semantics = load_semantics(join(grammar_dir, "gpsr_category_1_semantics.txt"))
cat2_semantics = load_semantics([join(grammar_dir, "gpsr_category_1_semantics.txt"), join(grammar_dir, "gpsr_category_2_semantics.txt")])
cat3_semantics = load_semantics(join(grammar_dir, "gpsr_category_3_semantics.txt"))


utterance, parse = generate_random_pair(ROOT_SYMBOL, cat1_rules, cat1_semantics, generator=random.Random())
print(tree_printer(utterance))