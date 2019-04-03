import os
from os.path import join

import random
from gpsr_semantic_parser.grammar import prepare_rules
from gpsr_semantic_parser.types import ROOT_SYMBOL
from gpsr_semantic_parser.generation import generate_sentences, generate_random_pair
from gpsr_semantic_parser.semantics import load_semantics
from gpsr_semantic_parser.util import tokens_to_str, assert_no_wildcards

grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2018")

common_path = join(grammar_dir, "common_rules.txt")

paths = tuple(map(lambda x: join(grammar_dir, x), ["objects.xml", "locations.xml", "names.xml", "gestures.xml"]))

cat1_rules = prepare_rules(common_path, join(grammar_dir, "gpsr_category_1_grammar.txt"), *paths)
cat2_rules = prepare_rules(common_path, join(grammar_dir, "gpsr_category_2_grammar.txt"), *paths)
cat3_rules = prepare_rules(common_path, join(grammar_dir, "gpsr_category_3_grammar.txt"), *paths)
cat1_semantics = load_semantics(join(grammar_dir, "gpsr_category_1_semantics.txt"))
cat2_semantics = load_semantics(
    [join(grammar_dir, "gpsr_category_1_semantics.txt"), join(grammar_dir, "gpsr_category_2_semantics.txt")])
cat3_semantics = load_semantics(join(grammar_dir, "gpsr_category_3_semantics.txt"))

grounded_examples = []
random_source = random.Random(0)
for generation_path, semantic_production in cat1_semantics.items():
    utterance, parse = generate_random_pair(list(generation_path), cat1_rules, cat1_semantics, random_source)
    assert_no_wildcards(utterance)
    grounded_examples.append((utterance, parse))

for generation_path, semantic_production in cat2_semantics.items():
    utterance, parse = generate_random_pair(list(generation_path), cat2_rules, cat2_semantics, random_source)
    assert_no_wildcards(utterance)
    grounded_examples.append((utterance, parse))

for generation_path, semantic_production in cat3_semantics.items():
    utterance, parse = generate_random_pair(list(generation_path), cat3_rules, cat3_semantics, random_source)
    assert_no_wildcards(utterance)
    grounded_examples.append((utterance, parse))


with open("../data/rephrasings_data.csv",'w') as output:
    output.write("command,semantics\n")
    for utterance, parse in grounded_examples:
        output.write("\"{}\",\"{}\"\n".format(tokens_to_str(utterance), str(parse)))