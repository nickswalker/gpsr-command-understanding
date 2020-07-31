import os
import sys
from random import Random

import numpy as np
from os.path import join
import re

from gpsr_command_understanding.generator.grammar import tree_printer
from gpsr_command_understanding.generator.loading_helpers import load, GRAMMAR_YEAR_TO_MODULE
from gpsr_command_understanding.generator.tokens import ROOT_SYMBOL
from gpsr_command_understanding.generator.paired_generator import pairs_without_placeholders, PairedGenerator


def get_annotated_sentences(sentences_and_pairs):
    sentences, pairs = sentences_and_pairs
    expanded_pairs = {tree_printer(key): tree_printer(value) for key, value in pairs.items()}
    # These came straight from the grammar
    grammar_sentences = set([tree_printer(x) for x in sentences])
    # These came from expanding the semantics, so they may not be in the grammar
    annotated_sentences = set(expanded_pairs.keys())
    # Only keep annotations that cover sentences actually in the grammar
    out_of_grammar = annotated_sentences.difference(grammar_sentences)
    annotated_sentences.intersection_update(grammar_sentences)
    unannotated_sentences = grammar_sentences.difference(annotated_sentences)
    return annotated_sentences, unannotated_sentences, out_of_grammar


def main():
    year = int(sys.argv[1])
    task = sys.argv[2]
    out_root = os.path.abspath(os.path.dirname(__file__) + "/../../data/")

    generator = PairedGenerator(None, grammar_format_version=year)
    load(generator, task, GRAMMAR_YEAR_TO_MODULE[year])

    sentences = [pair[0] for pair in
                 generator.generate(ROOT_SYMBOL, yield_requires_semantics=False)]
    [generator.extract_metadata(sentence) for sentence in sentences]
    sentences = set(sentences)

    out_path = join(out_root, "{}_{}_sentences.txt".format(year, task))
    with open(out_path, "w") as f:
        for sentence in sentences:
            f.write(tree_printer(sentence) + '\n')

    baked_sentences = [tree_printer(x) for x in sentences]
    all_pairs = pairs_without_placeholders(generator)
    baked_pairs = {tree_printer(key): tree_printer(value) for key, value in all_pairs.items()}

    annotated, unannotated, out_of_grammar = get_annotated_sentences((sentences, all_pairs))

    unique_sentence_parses = [all_pairs[ann_sen] for ann_sen in annotated]
    unique_sentence_parses = [set(x) for x in unique_sentence_parses]

    out_path = join(out_root, "{}_{}_pairs.txt".format(year, task))

    with open(out_path, "w") as f:
        for sentence, parse in baked_pairs.items():
            f.write(sentence + '\n' + parse + '\n')

    meta_out_path = join(out_root, "{}_{}_annotations_meta.txt".format(year, task))
    with open(meta_out_path, "w") as f:
        f.write("Coverage:\n")
        f.write("{0}/{1} {2:.1f}%\n".format(len(annotated), len(baked_sentences),
                                            100.0 * len(annotated) / len(baked_sentences)))
        f.write("\t unique parses: {}\n".format(len(unique_sentence_parses)))
        sen_lengths = [len(sentence.split()) for sentence, logical in baked_pairs]
        avg_sentence_length = np.mean(sen_lengths)
        parse_lengths = []
        filtered_parse_lengths = []
        for parse in unique_sentence_parses:
            parse_lengths.append(len(parse.split()))
            stop_tokens_removed = re.sub(r"(\ e\ |\"|\)|\()", "", parse)
            filtered_parse_lengths.append(len(stop_tokens_removed.split()))
        avg_parse_length = np.mean(parse_lengths)
        avg_filtered_parse_length = np.mean(filtered_parse_lengths)
        f.write(
            "\t avg sentence length (tokens): {:.1f} avg parse length (tokens): {:.1f} avg filtered parse length (tokens): {:.1f}\n".format(
                avg_sentence_length, avg_parse_length, avg_filtered_parse_length))

    """print("No parses for:")
    for sentence in sorted(unannotated):
        print(sentence)
    print("-----------------")"""


if __name__ == "__main__":
    main()
