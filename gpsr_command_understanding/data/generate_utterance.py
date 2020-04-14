from gpsr_command_understanding.generator.grammar import tree_printer
from gpsr_command_understanding.generator.loading_helpers import load_all_2018_by_cat, GRAMMAR_DIR_2018
from gpsr_command_understanding.generator.tokens import ROOT_SYMBOL
from gpsr_command_understanding.generator.generation import generate_random_pair

import random

generator = load_all_2018_by_cat(GRAMMAR_DIR_2018)

utterance, parse = generate_random_pair(ROOT_SYMBOL, generator, random_generator=random.Random())
print(tree_printer(utterance))
