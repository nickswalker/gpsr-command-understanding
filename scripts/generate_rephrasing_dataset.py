import os
from os.path import join
import random
import csv

from gpsr_semantic_parser.grammar import prepare_grounded_rules, tree_printer, prepare_anonymized_rules, load_grammar
from gpsr_semantic_parser.generation import generate_random_pair, expand_pair_full
from gpsr_semantic_parser.semantics import load_semantics, lambda_parser
from gpsr_semantic_parser.util import has_placeholders

grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2018")

common_path = join(grammar_dir, "common_rules.txt")

paths = tuple(map(lambda x: join(grammar_dir, x), ["objects.xml", "locations.xml", "names.xml", "gestures.xml"]))

cat1_rules = load_grammar([common_path, join(grammar_dir, "gpsr_category_1_grammar.txt")])
cat2_rules = load_grammar([common_path, join(grammar_dir, "gpsr_category_2_grammar.txt")])
cat3_rules = load_grammar([common_path, join(grammar_dir, "gpsr_category_3_grammar.txt")])

cat1_rules_ground = prepare_grounded_rules(common_path, join(grammar_dir, "gpsr_category_1_grammar.txt"), *paths)
cat2_rules_ground = prepare_grounded_rules(common_path, join(grammar_dir, "gpsr_category_2_grammar.txt"), *paths)
cat3_rules_ground = prepare_grounded_rules(common_path, join(grammar_dir, "gpsr_category_3_grammar.txt"), *paths)
cat1_rules_anon = prepare_anonymized_rules(common_path, join(grammar_dir, "gpsr_category_1_grammar.txt"))
cat2_rules_anon = prepare_anonymized_rules(common_path, join(grammar_dir, "gpsr_category_2_grammar.txt"))
cat3_rules_anon = prepare_anonymized_rules(common_path, join(grammar_dir, "gpsr_category_3_grammar.txt"))

cat1_semantics = load_semantics(join(grammar_dir, "gpsr_category_1_semantics.txt"))
cat2_semantics = load_semantics(
    [join(grammar_dir, "gpsr_category_1_semantics.txt"), join(grammar_dir, "gpsr_category_2_semantics.txt")])
cat3_semantics = load_semantics(join(grammar_dir, "gpsr_category_3_semantics.txt"))

grounded_examples = []
random_source = random.Random(0)
for generation_path, semantic_production in cat1_semantics.items():
    utterance_wild, parse_wild = generate_random_pair(generation_path, cat1_rules, cat1_semantics, yield_requires_semantics=True, generator=random_source)
    _, parse_anon = expand_pair_full(utterance_wild, parse_wild, cat1_rules_anon, branch_cap=1, generator=random_source)
    utterance, parse_ground = expand_pair_full(utterance_wild, parse_wild, cat1_rules_ground, branch_cap=1, generator=random_source)
    assert not has_placeholders(utterance)
    lambda_parser.parse(tree_printer(parse_ground))
    grounded_examples.append((utterance, parse_anon, parse_ground))

for generation_path, semantic_production in cat2_semantics.items():
    utterance_wild, parse_wild = generate_random_pair(generation_path, cat2_rules, cat2_semantics, yield_requires_semantics=True, generator=random_source)
    _, parse_anon = expand_pair_full(utterance_wild, parse_wild, cat2_rules_anon, branch_cap=1, generator=random_source)
    utterance, parse_ground = expand_pair_full(utterance_wild, parse_wild, cat2_rules_ground, branch_cap=1, generator=random_source)
    assert not has_placeholders(utterance)
    lambda_parser.parse(tree_printer(parse_ground))
    grounded_examples.append((utterance, parse_anon, parse_ground))

for generation_path, semantic_production in cat3_semantics.items():
    utterance_wild, parse_wild = generate_random_pair(generation_path, cat3_rules, cat3_semantics, yield_requires_semantics=True, generator=random_source)
    _, parse_anon = expand_pair_full(utterance_wild, parse_wild, cat3_rules_anon, branch_cap=1, generator=random_source)
    utterance, parse_ground = expand_pair_full(utterance_wild, parse_wild, cat3_rules_ground, branch_cap=1, generator=random_source)
    assert not has_placeholders(utterance)
    lambda_parser.parse(tree_printer(parse_ground))
    grounded_examples.append((utterance, parse_anon, parse_ground))

random_source.shuffle(grounded_examples)
def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


with open("../data/rephrasings_data.csv",'w') as csvfile:
    output = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
    command_columns = [("command" + str(x), "parse" + str(x), "parse_ground" + str(x)) for x in range(1,13)]
    command_columns = [x for tuple in command_columns for x in tuple]
    output.writerow(command_columns)

    for chunk in chunker(grounded_examples,12):
        line = []
        for utterance, parse_anon, parse_ground in chunk:
            line += [tree_printer(utterance), tree_printer(parse_anon), tree_printer(parse_ground)]
        output.writerow(line)

# Let's verify that we can load the output back in...
with open("../data/rephrasings_data.csv",'r') as csvfile:
    input = csv.DictReader(csvfile)
    for line in input:
        pass
        #print(line)