import os
import sys
from os.path import join

from gpsr_semantic_parser.grammar import load_wildcard_rules, parse_production_rules, get_wildcards, make_mock_wildcard_rules, tokenize
from gpsr_semantic_parser.types import ROOT_SYMBOL
from gpsr_semantic_parser.generation import generate_sentences, generate_sentence_parse_pairs
from gpsr_semantic_parser.semantics import load_semantics
from gpsr_semantic_parser.util import merge_dicts, tokens_to_text

grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../resources")

rules = parse_production_rules([join(grammar_dir, path) for path in ["common_rules.txt", "gpsr_category_1_grammar.txt"]])
groundable_terms = get_wildcards(rules)
grounding_rules = make_mock_wildcard_rules(groundable_terms)
# There are too many wildcard options for this to workable during testing
#grounding_rules = load_wildcard_rules(join(grammar_dir, "objects.xml"),join(grammar_dir, "locations.xml"),join(grammar_dir, "names.xml"))
rules = merge_dicts(rules, grounding_rules)
semantics = load_semantics([join(grammar_dir, "gpsr_category_1_semantics.txt")])

sentences = generate_sentences(ROOT_SYMBOL, rules)
sentence_parse_pairs = generate_sentence_parse_pairs(ROOT_SYMBOL, rules, semantics)
#sentence_parse_pairs = generate_sentence_parse_pairs(tokenize("$vbbring me the {kobject} from the {placement}"), rules, semantics)
#sentence_parse_pairs = generate_sentence_parse_pairs(tokenize("$fndppl "), rules, semantics)

sentences_out_path = "/tmp/all_sentences.txt"
pairs_out_path = "/tmp/all_pairs.txt"
if os.path.isfile(sentences_out_path):
    os.remove(sentences_out_path)
if os.path.isfile(pairs_out_path):
    os.remove(pairs_out_path)

with open(sentences_out_path, "w") as f:
    for sentence in sentences:
        sentence_string = tokens_to_text(sentence)
        f.write(sentence_string + '\n')

with open(pairs_out_path, "w") as f:
    for sentence, parse in sentence_parse_pairs:
        sentence_string = tokens_to_text(sentence)
        f.write(sentence_string + '\n')
        parse_string = str(parse) if parse else "None"
        f.write(parse_string + '\n')
        f.write('\n')