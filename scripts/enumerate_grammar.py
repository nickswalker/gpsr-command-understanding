import itertools
import os
import sys
from os.path import join

from gpsr_semantic_parser.grammar import prepare_anonymized_rules
from gpsr_semantic_parser.types import ROOT_SYMBOL
from gpsr_semantic_parser.generation import generate_sentences, expand_all_semantics
from gpsr_semantic_parser.semantics import load_semantics
from gpsr_semantic_parser.util import tokens_to_str

out_root = os.path.abspath(os.path.dirname(__file__) + "/../data")
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

cat1_pairs = expand_all_semantics(cat1_rules, cat1_semantics)
cat1_pairs = {tokens_to_str(utterance): str(parse) for utterance, parse in cat1_pairs}

cat2_pairs = expand_all_semantics(cat2_rules, cat2_semantics)
cat2_pairs = {tokens_to_str(utterance): str(parse) for utterance, parse in cat2_pairs}

cat3_pairs = expand_all_semantics(cat3_rules, cat3_semantics)
cat3_pairs = {tokens_to_str(utterance): str(parse) for utterance, parse in cat3_pairs}


cat1_sentences = set([tokens_to_str(x) for x in cat1_sentences])
cat2_sentences = set([tokens_to_str(x) for x in cat2_sentences])
cat2_sentences_unique = cat2_sentences.difference(cat1_sentences)
cat3_sentences = set([tokens_to_str(x) for x in cat3_sentences])
cat3_sentences_unique = cat3_sentences.difference(cat1_sentences).difference(cat2_sentences)

all_sentences = cat1_sentences.union(cat2_sentences).union(cat3_sentences)

cat1_annotated_sentences = set(cat1_pairs.keys())
# Only keep annotations that cover sentences actually in the grammar
cat1_annotated_sentences.intersection_update(cat1_sentences)
cat1_parses = set(cat1_pairs.values())

cat2_annotated_sentences = set(cat2_pairs.keys())
cat2_annotated_sentences.intersection_update(cat2_sentences)
cat2_with_parse_unique = cat2_annotated_sentences.difference(cat1_sentences)
cat2_parses = set(cat2_pairs.values()).difference(cat1_parses)

cat3_annotated_sentences = set(cat3_pairs.keys())
cat3_annotated_sentences.intersection_update(cat3_sentences)
cat3_with_parse_unique = cat3_annotated_sentences.difference(cat1_sentences).difference(cat2_sentences)
cat3_parses = set(cat3_pairs.values()).difference(cat2_parses).difference(cat1_parses)

combined_annotations = cat1_annotated_sentences.union(cat2_annotated_sentences).union(cat3_annotated_sentences)
combined_annotations.intersection_update(all_sentences)

cat1_parseless = cat1_sentences.difference(cat1_annotated_sentences)
cat2_parseless = cat2_sentences.difference(cat2_annotated_sentences)
cat3_parseless = cat3_sentences.difference(cat3_annotated_sentences)

#sentence_parse_pairs = generate_sentence_parse_pairs(ROOT_SYMBOL, cat1_rules, cat1_semantics)

sentences1_out_path = join(out_root, "1_sentences.txt")
sentences2_out_path = join(out_root, "2_sentences.txt")
sentences3_out_path = join(out_root, "3_sentences.txt")

for cat_out_path, sentences in zip([sentences1_out_path, sentences2_out_path, sentences3_out_path],[cat1_sentences, cat2_sentences, cat3_sentences]):
    with open(cat_out_path, "w") as f:
        for sentence in sentences:
            f.write(sentence + '\n')

pairs1_out_path = join(out_root, "1_pairs.txt")
pairs2_out_path = join(out_root, "2_pairs.txt")
pairs3_out_path = join(out_root, "3_pairs.txt")
cat1_pairs = expand_all_semantics(cat1_rules, cat1_semantics)
cat2_pairs = expand_all_semantics(cat2_rules, cat2_semantics)
cat3_pairs = expand_all_semantics(cat3_rules, cat3_semantics)
for cat_out_path, pairs in zip([pairs1_out_path, pairs2_out_path, pairs3_out_path],[cat1_pairs, cat2_pairs, cat3_pairs]):
    with open(cat_out_path, "w") as f:
        for sentence, parse in pairs:
            f.write(tokens_to_str(sentence) + '\n' + str(parse) + '\n')

meta_out_path = join(out_root, "annotations_meta.txt")
with open(meta_out_path, "w") as f:
    f.write("Coverage:\n")
    f.write("cat1 {0}/{1} {2:.1f}%\n".format(len(cat1_annotated_sentences), len(cat1_sentences), 100.0 * len(cat1_annotated_sentences) / len(cat1_sentences)))
    f.write("\t unique parses: {}\n".format(len(cat1_parses)))
    f.write("cat2 {0}/{1} {2:.1f}%\n".format(len(cat2_annotated_sentences), len(cat2_sentences), 100.0 * len(cat2_annotated_sentences) / len(cat2_sentences)))
    f.write("\t unique {0}/{1} {2:.1f}%\n".format(len(cat2_with_parse_unique), len(cat2_sentences_unique), 100.0 * len(cat2_with_parse_unique) / len(cat2_sentences_unique)))
    f.write("\t unique parses: {}\n".format(len(cat2_parses)))
    f.write("cat3 {0}/{1} {2:.1f}%\n".format(len(cat3_annotated_sentences), len(cat3_sentences), 100.0 * len(cat3_annotated_sentences) / len(cat3_sentences)))
    f.write("\t unique {0}/{1} {2:.1f}%\n".format(len(cat3_with_parse_unique), len(cat3_sentences_unique), 100.0 * len(cat3_with_parse_unique) / len(cat3_sentences_unique)))
    f.write("\t unique parses: {}\n".format(len(cat3_parses)))

    f.write("combined {0}/{1} {2:.1f}%\n".format(len(combined_annotations), len(all_sentences), 100.0 * len(combined_annotations) / len(all_sentences)))
    f.write("combined unique parses: {}".format(len(cat1_parses.union(cat2_parses).union(cat3_parses))))

print("No parses for:")
print("Cat 1:")
for sentence in sorted(cat1_parseless):
    print(sentence)
print("\n---------------------------------------\nCat 2:")
for sentence in sorted(cat2_parseless):
    print(sentence)
print("\n---------------------------------------\nCat 3:")
for sentence in sorted(cat3_parseless):
    print(sentence)