import itertools
import os
import numpy as np
from os.path import join

from gpsr_semantic_parser.generator import Generator
from gpsr_semantic_parser.grammar import tree_printer
from gpsr_semantic_parser.loading_helpers import load_all_2018
from gpsr_semantic_parser.tokens import ROOT_SYMBOL
from gpsr_semantic_parser.generation import generate_sentences, expand_all_semantics
from gpsr_semantic_parser.util import has_placeholders

out_root = os.path.abspath(os.path.dirname(__file__) + "/../../data")
grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../../resources/generator2018")

cmd_gen = Generator(grammar_format_version=2018)
generator = load_all_2018(cmd_gen, grammar_dir)


def get_annotated_sentences(sentences_and_pairs):
    sentences, pairs = sentences_and_pairs
    annotated_sentences = set(pairs.keys())
    # Only keep annotations that cover sentences actually in the grammar
    useless_annotations = annotated_sentences.difference(sentences)
    annotated_sentences.intersection_update(sentences)
    return annotated_sentences


cat_sentences = [set(generate_sentences(ROOT_SYMBOL, rules)) for _,rules, _, _ in generator]
pairs = [{utterance: parse for utterance, parse in expand_all_semantics(rules, semantics)} for _, rules, _, semantics in generator]
unique = []
for i, _ in enumerate(cat_sentences):
    prev_cats = cat_sentences[:i]
    if prev_cats:
    # Don't count the sentence as unique unless it hasn't happened in any earlier categories
        unique.append(cat_sentences[i].difference())
    else:
        unique.append(cat_sentences[i])

all_sentences = set().union(*cat_sentences)
all_pairs = pairs

annotated = [get_annotated_sentences(x) for x in zip(cat_sentences, pairs)]

unique_annotated = [get_annotated_sentences((unique_sen, cat_pairs)) for unique_sen, cat_pairs in zip(unique, pairs)]
unique_sentence_parses = [[pairs[ann_sen] for ann_sen in annotated] for annotated, pairs in zip(unique_annotated, pairs)]
unique_sentence_parses = [set(x) for x in unique_sentence_parses]

combined_annotations = set().union(*annotated)
combined_annotations.intersection_update(all_sentences)

parseless = [sen.difference(annotated_sentences) for sen, annotated_sentences in zip(cat_sentences, annotated)]

out_paths = [join(out_root, str(i)+"_sentences.txt") for i in range(1, 4)]

for cat_out_path, sentences in zip(out_paths,cat_sentences):
    with open(cat_out_path, "w") as f:
        for sentence in sentences:
            assert not has_placeholders(sentence)
            f.write(tree_printer(sentence) + '\n')

out_paths = [join(out_root, str(i)+"_pairs.txt") for i in range(1, 4)]


for cat_out_path, pairs in zip(out_paths,all_pairs):
    with open(cat_out_path, "w") as f:
        for sentence, parse in pairs.items():
            if has_placeholders(sentence) or has_placeholders(parse):
                print("Skipping pair for {} because it still has placeholders after expansion".format(tree_printer(sentence)))
                continue
            f.write(tree_printer(sentence) + '\n' + tree_printer(parse) + '\n')

meta_out_path = join(out_root, "annotations_meta.txt")
with open(meta_out_path, "w") as f:
    f.write("Coverage:\n")
    cat_parse_lengths = []
    cat_sen_lengths = []
    for i, (annotated_sen, sen, unique_parses) in enumerate(zip(annotated, cat_sentences, unique_sentence_parses)):
        f.write("cat{0} {1}/{2} {3:.1f}%\n".format(i+1, len(annotated_sen), len(sen), 100.0 * len(annotated_sen) / len(sen)))
        f.write("\t unique parses: {}\n".format(len(unique_parses)))
        cat_sen_lengths.append([len(tree_printer(sentence).split(" ")) for sentence in sen])
        avg_sentence_length = np.mean(cat_sen_lengths[i])
        cat_parse_lengths.append([len(tree_printer(parse).split(" ")) for parse in unique_parses])
        avg_parse_length = np.mean(cat_parse_lengths[i])
        f.write("\t avg sentence length (tokens): {:.2f} avg parse length (tokens): {:.2f}\n".format(avg_sentence_length, avg_parse_length))


    f.write("combined {0}/{1} {2:.1f}%\n".format(len(combined_annotations), len(all_sentences), 100.0 * len(combined_annotations) / len(all_sentences)))
    f.write("combined unique parses: {}\n".format(len(set().union(*unique_sentence_parses))))

    all_sen_lengths = [length for cat in cat_sen_lengths for length in cat]
    all_parse_lengths = [length for cat in cat_parse_lengths for length in cat]
    f.write("combined avg sentence length (tokens): {:.2f} avg parse length (tokens): {:.2f}\n".format(np.mean(all_sen_lengths), np.mean(all_parse_lengths)))
print("No parses for:")
for cat in parseless:
    for sentence in sorted(map(tree_printer, cat)):
        print(sentence)
    print("-----------------")