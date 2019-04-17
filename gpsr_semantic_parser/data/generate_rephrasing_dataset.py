import os
import random
import csv

from gpsr_semantic_parser.generator import Generator
from gpsr_semantic_parser.grammar import tree_printer
from gpsr_semantic_parser.loading_helpers import load_all_2018
from gpsr_semantic_parser.generation import generate_random_pair, expand_pair_full
from gpsr_semantic_parser.util import has_placeholders

random_source = random.Random(0)
grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../../resources/generator2018")

cmd_gen = Generator(grammar_format_version=2018)
generator = load_all_2018(cmd_gen, grammar_dir)

rehprasings_per_hit = 12
groundings_per_parse = 3


def get_grounding_per_each_parse(generator):
    grounded_examples = []

    for rules, rules_anon, rules_ground, semantics in generator:
        for generation_path, semantic_production in semantics.items():
            utterance_wild, parse_wild = generate_random_pair(generation_path, rules, semantics, yield_requires_semantics=True, generator=random_source)
            _, parse_anon = expand_pair_full(utterance_wild, parse_wild, rules_anon, branch_cap=1, generator=random_source)
            utterance, parse_ground = expand_pair_full(utterance_wild, parse_wild, rules_ground, branch_cap=1, generator=random_source)
            assert not has_placeholders(utterance)
            cmd_gen.lambda_parser.parse(tree_printer(parse_ground))
            grounded_examples.append((utterance, parse_anon, parse_ground))
    return grounded_examples


all_examples = []
for i in range(groundings_per_parse):
    grounded_examples = get_grounding_per_each_parse(generator)
    random_source.shuffle(grounded_examples)
    all_examples += grounded_examples


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


with open(os.path.abspath(os.path.dirname(__file__) +"/../../data/rephrasings_data.csv"),'w') as csvfile:
    output = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
    command_columns = [("command" + str(x), "parse" + str(x), "parse_ground" + str(x)) for x in range(1,rehprasings_per_hit + 1)]
    command_columns = [x for tuple in command_columns for x in tuple]
    output.writerow(command_columns)

    chunks = list(chunker(all_examples,rehprasings_per_hit))
    print("Writing {} HITS".format(len(chunks)))
    for chunk in chunks:
        line = []
        for utterance, parse_anon, parse_ground in chunk:
            line += [tree_printer(utterance), tree_printer(parse_anon), tree_printer(parse_ground)]
        output.writerow(line)

# Let's verify that we can load the output back in...
with open(os.path.abspath(os.path.dirname(__file__) +"/../../data/rephrasings_data.csv"),'r') as csvfile:
    input = csv.DictReader(csvfile)
    for line in input:
        pass
        #print(line)