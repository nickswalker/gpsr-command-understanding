import itertools
import os
import random
from os.path import join

from gpsr_semantic_parser.types import ROOT_SYMBOL
from gpsr_semantic_parser.generation import generate_sentences, expand_all_semantics
from gpsr_semantic_parser.semantics import load_semantics
from gpsr_semantic_parser.util import tokens_to_str
from gpsr_semantic_parser.grammar import prepare_rules

grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../resources")
common_path = join(grammar_dir, "common_rules.txt")

cat2_rules = prepare_rules(common_path, join(grammar_dir,"gpsr_category_2_grammar.txt"))
cat2_semantics = load_semantics([join(grammar_dir, "gpsr_category_1_semantics.txt"), join(grammar_dir, "gpsr_category_2_semantics.txt")])
cat2_pairs = expand_all_semantics(cat2_rules, cat2_semantics)

all_unique_pairs = {}
for utterance, parse in itertools.chain(cat2_pairs):
    all_unique_pairs[tokens_to_str(utterance)] = parse
pairs_out_path = os.path.join(os.path.abspath(os.path.dirname(__file__) + "/.."), "data")
test_out_path = os.path.join(pairs_out_path, "test.txt")

all_pairs = list(all_unique_pairs.items())
test = sorted(all_pairs, key=lambda x: len(x[0]))
with open(test_out_path, "w") as f:
    for sentence, parse in test:
        f.write(sentence + '\n' + str(parse) + '\n')
