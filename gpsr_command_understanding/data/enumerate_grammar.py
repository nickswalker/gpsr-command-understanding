import os
import numpy as np
from os.path import join
import re

from gpsr_command_understanding.grammar import tree_printer, DiscardMeta
from gpsr_command_understanding.loading_helpers import load_all_2018_by_cat, GRAMMAR_DIR_2018
from gpsr_command_understanding.tokens import ROOT_SYMBOL
from gpsr_command_understanding.generation import generate_sentences, pairs_without_placeholders
from gpsr_command_understanding.util import determine_unique_cat_data


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
    out_root = os.path.abspath(os.path.dirname(__file__) + "/../../data")

    generators = load_all_2018_by_cat(GRAMMAR_DIR_2018)

    cat_sentences = [set(generate_sentences(ROOT_SYMBOL, generator)) for generator in generators]
    stripper = DiscardMeta()
    cat_sentences = [set([stripper.visit(sentence) for sentence in cat]) for cat in cat_sentences]
    all_sentences = [tree_printer(x) for x in set().union(*cat_sentences)]
    all_pairs = [pairs_without_placeholders(generator) for generator in generators]
    baked_pairs = [{tree_printer(key): tree_printer(value) for key, value in pairs.items()} for pairs in all_pairs]

    by_utterance, by_parse = determine_unique_cat_data(all_pairs, keep_new_utterance_repeat_parse_for_lower_cat=False)
    unique = []
    for i, _ in enumerate(cat_sentences):
        prev_cats = cat_sentences[:i]
        if prev_cats:
        # Don't count the sentence as unique unless it hasn't happened in any earlier categories
            prev_cat_sentences = set().union(*prev_cats)
            overlapped_with_prev = cat_sentences[i].intersection(prev_cat_sentences)
            unique.append(cat_sentences[i].difference(prev_cat_sentences))
        else:
            unique.append(cat_sentences[i])
    # Sets should be disjoint
    assert (len(set().union(*unique)) == sum([len(cat) for cat in unique]))

    stats = [get_annotated_sentences(x) for x in zip(cat_sentences, all_pairs)]
    annotated, unannotated, out_of_grammar = [c[0] for c in stats], [c[1] for c in stats], [c[2] for c in stats]

    unique_annotated = [get_annotated_sentences((unique_sen, cat_pairs))[0] for unique_sen, cat_pairs in zip(unique, all_pairs)]
    unique_sentence_parses = [[pairs[ann_sen] for ann_sen in annotated] for annotated, pairs in zip(unique_annotated, baked_pairs)]
    unique_sentence_parses = [set(x) for x in unique_sentence_parses]

    combined_annotations = set().union(*annotated)
    combined_annotations.intersection_update(all_sentences)
    # Note that this won't actually catch the correct unannotated; the expansion order of the sentence may
    # fail to hit the exact match for the semantics annotation that is required
    #parseless_another_way = [list(filter(lambda pair: pair[1] is None, generate_sentence_parse_pairs(NonTerminal("deliver"), gen, yield_requires_semantics=False))) for gen in generators]

    out_paths = [join(out_root, str(i)+"_sentences.txt") for i in range(1, 4)]

    for cat_out_path, sentences in zip(out_paths,cat_sentences):
        with open(cat_out_path, "w") as f:
            for sentence in sentences:
                f.write(tree_printer(sentence) + '\n')

    out_paths = [join(out_root, str(i)+"_pairs.txt") for i in range(1, 4)]

    for cat_out_path, pairs in zip(out_paths,baked_pairs):
        with open(cat_out_path, "w") as f:
            for sentence, parse in pairs.items():
                f.write(sentence + '\n' + parse + '\n')

    meta_out_path = join(out_root, "annotations_meta.txt")
    with open(meta_out_path, "w") as f:
        f.write("Coverage:\n")
        cat_parse_lengths = []
        cat_filtered_parse_lengths = []
        cat_sen_lengths = []
        for i, (annotated_sen, sen, unique_parses) in enumerate(zip(annotated, cat_sentences, unique_sentence_parses)):
            f.write("cat{0} {1}/{2} {3:.1f}%\n".format(i+1, len(annotated_sen), len(sen), 100.0 * len(annotated_sen) / len(sen)))
            f.write("\t unique parses: {}\n".format(len(unique_parses)))
            cat_sen_lengths.append([len(tree_printer(sentence).split()) for sentence in sen])
            avg_sentence_length = np.mean(cat_sen_lengths[i])
            parse_lengths = []
            filtered_parse_lengths = []
            for parse in unique_parses:
                parse_lengths.append(len(parse.split()))
                stop_tokens_removed = re.sub("(\ e\ |\"|\)|\()", "", parse)
                filtered_parse_lengths.append(len(stop_tokens_removed.split()))
            cat_parse_lengths.append(parse_lengths)
            cat_filtered_parse_lengths.append(filtered_parse_lengths)
            avg_parse_length = np.mean(cat_parse_lengths[i])
            avg_filtered_parse_length = np.mean(cat_filtered_parse_lengths[i])
            f.write(
                "\t avg sentence length (tokens): {:.1f} avg parse length (tokens): {:.1f} avg filtered parse length (tokens): {:.1f}\n".format(
                    avg_sentence_length, avg_parse_length, avg_filtered_parse_length))

        f.write("combined {0}/{1} {2:.1f}%\n".format(len(combined_annotations), len(all_sentences), 100.0 * len(combined_annotations) / len(all_sentences)))
        f.write("combined unique parses: {}\n".format(len(set().union(*unique_sentence_parses))))

        all_sen_lengths = [length for cat in cat_sen_lengths for length in cat]
        all_parse_lengths = [length for cat in cat_parse_lengths for length in cat]
        all_filtered_parse_lengths = [length for cat in cat_filtered_parse_lengths for length in cat]
        f.write(
            "combined avg sentence length (tokens): {:.1f} avg parse length (tokens): {:.1f} avg filtered parse length (tokens): {:.1f}\n".format(
                np.mean(all_sen_lengths), np.mean(all_parse_lengths), np.mean(all_filtered_parse_lengths)))
    print("No parses for:")
    for cat in unannotated:
        for sentence in sorted(cat):
            print(sentence)
        print("-----------------")


if __name__ == "__main__":
    main()