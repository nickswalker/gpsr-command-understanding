import itertools
import os
import sys
from os.path import join

from gpsr_semantic_parser.grammar import prepare_anonymized_rules
from gpsr_semantic_parser.types import ROOT_SYMBOL
from gpsr_semantic_parser.generation import generate_sentences, generate_sentence_parse_pairs, \
    generate_sentence_parse_pairs_exhaustive, expand_all_semantics
from gpsr_semantic_parser.semantics import load_semantics
from gpsr_semantic_parser.util import tokens_to_str

grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2018")
common_path = join(grammar_dir, "common_rules.txt")

cat1_rules = prepare_anonymized_rules(common_path, join(grammar_dir, "gpsr_category_1_grammar.txt"))
cat2_rules = prepare_anonymized_rules(common_path, join(grammar_dir, "gpsr_category_2_grammar.txt"))
cat3_rules = prepare_anonymized_rules(common_path, join(grammar_dir, "gpsr_category_3_grammar.txt"))
cat1_semantics = load_semantics(join(grammar_dir, "gpsr_category_1_semantics.txt"))
cat2_semantics = load_semantics([join(grammar_dir, "gpsr_category_1_semantics.txt"), join(grammar_dir, "gpsr_category_2_semantics.txt")])
cat3_semantics = load_semantics(join(grammar_dir, "gpsr_category_3_semantics.txt"))

cat1_sentences = generate_sentences(ROOT_SYMBOL, cat1_rules)
cat2_sentences = generate_sentences(ROOT_SYMBOL, cat2_rules)
cat3_sentences = generate_sentences(ROOT_SYMBOL, cat3_rules)
#sentence_parse_pairs = generate_sentence_parse_pairs(ROOT_SYMBOL, cat1_rules, cat1_semantics)


sentences_out_path = "/tmp/all_sentences.txt"
pairs_out_path = "/tmp/all_pairs.txt"
if os.path.isfile(sentences_out_path):
    os.remove(sentences_out_path)
if os.path.isfile(pairs_out_path):
    os.remove(pairs_out_path)

with open(sentences_out_path, "w") as f:
    for sentence in cat1_sentences:
        f.write(tokens_to_str(sentence) + '\n')
    f.write("----\n")
    for sentence in cat2_sentences:
        f.write(tokens_to_str(sentence) + '\n')
    f.write("----\n")
    for sentence in cat3_sentences:
        f.write(tokens_to_str(sentence) + '\n')

cat1_pairs = expand_all_semantics(cat1_rules, cat1_semantics)
cat2_pairs = expand_all_semantics(cat2_rules, cat2_semantics)
cat3_pairs = expand_all_semantics(cat3_rules, cat3_semantics)

with open(pairs_out_path, "w") as f:
    for sentence, parse in cat1_pairs:
        f.write(tokens_to_str(sentence) + '\n' + str(parse) + '\n')
    f.write("----\n")
    for sentence, parse in cat2_pairs:
        f.write(tokens_to_str(sentence) + '\n' + str(parse) + '\n')
    f.write("----\n")
    for sentence, parse in cat3_pairs:
        f.write(tokens_to_str(sentence) + '\n' + str(parse) + '\n')