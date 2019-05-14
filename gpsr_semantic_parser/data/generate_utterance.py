import os
from os.path import join

from gpsr_semantic_parser.generator import Generator
from gpsr_semantic_parser.grammar import  tree_printer
from gpsr_semantic_parser.loading_helpers import load_all_2018
from gpsr_semantic_parser.tokens import ROOT_SYMBOL
from gpsr_semantic_parser.generation import generate_random_pair

import random

grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../../resources/generator2018/")
common_path = join(grammar_dir, "common_rules.txt")

paths = tuple(map(lambda x: join(grammar_dir, x), ["objects.xml", "locations.xml", "names.xml", "gestures.xml"]))

generator = Generator()
rules = load_all_2018(generator, grammar_dir)

utterance, parse = generate_random_pair(ROOT_SYMBOL, rules[0][1], rules[0][3], random_generator=random.Random())
print(tree_printer(utterance))