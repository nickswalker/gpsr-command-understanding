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

train_out_path = os.path.join(pairs_out_path, "train")

val_out_path = os.path.join(pairs_out_path, "val.txt")
test_out_path = os.path.join(pairs_out_path, "test.txt")

# Randomize for the split, but then sort by utterance length before we save out so that things are easier to read
all_pairs = list(all_unique_pairs.items())
random.Random(0).shuffle(all_pairs)
split1 = int(0.50 * len(all_pairs))
split2 = int(0.80 * len(all_pairs))
stuff, test = all_pairs[:split1], all_pairs[split1:]
train, val = stuff[:split2], stuff[split2:]

train = sorted(train, key=lambda x: len(x[0]))
val = sorted(val, key=lambda x: len(x[0]))
test = sorted(test, key=lambda x: len(x[0]))

with open(val_out_path, "w") as f:
    for sentence, parse in val:
        f.write(sentence + '\n' + str(parse) + '\n')

with open(test_out_path, "w") as f:
    for sentence, parse in test:
        f.write(sentence + '\n' + str(parse) + '\n')

limit = 16
count = 1
while limit < len(train):
    data_to_write = train[:limit]
    with open(train_out_path + str(count) + ".txt", "w") as f:
        for sentence, parse in data_to_write:
            f.write(sentence + '\n' + str(parse) + '\n')
    limit += 16
    count += 1
with open(train_out_path + "Full" + ".txt", "w") as f:
    for sentence, parse in train:
        f.write(sentence + '\n' + str(parse) + '\n')
