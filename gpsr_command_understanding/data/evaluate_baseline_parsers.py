#!/usr/bin/env python
import itertools
import os
import sys
import editdistance

from gpsr_command_understanding.generator import Generator

from gpsr_command_understanding.loading_helpers import load_all_2018
from gpsr_command_understanding.models.noop_tokenizer import NoOpTokenizer
from gpsr_command_understanding.models.seq2seq_data_reader import Seq2SeqDatasetReader
from gpsr_command_understanding.parser import AnonymizingParser, KNearestNeighborParser, GrammarBasedParser
from gpsr_command_understanding.anonymizer import Anonymizer
from nltk.metrics.distance import edit_distance, jaccard_distance

GRAMMAR_DIR = os.path.abspath(os.path.dirname(__file__) + "/../../resources/generator2018")


def bench_parser(parser, pairs):
    correct = 0
    parsed = 0
    for utterance, gold in pairs:
        pred = parser(utterance)
        if pred == gold:
            correct += 1
        if pred:
            parsed += 1
    return correct, parsed


def sweep_thresh(neighbors, test_pairs, anonymizer, metric, thresh_vals=range(0, 50)):
    num_paraphrases = len(test_pairs)
    for thresh in thresh_vals:
        anon_edit_distance_parser = KNearestNeighborParser(neighbors, k=1, distance_threshold=thresh, metric=metric)
        anon_edit_distance_parser = AnonymizingParser(anon_edit_distance_parser, anonymizer)
        correct, parsed = bench_parser(anon_edit_distance_parser, test_pairs)

        percent_correct = 100.0 * float(correct) / num_paraphrases
        if parsed == 0:
            percent_of_considered = 0.0
        else:
            percent_of_considered = 100.0 * float(correct) / parsed
        print("thresh={0} {1} out of total {2} correctly ({3:.2f}%). {4} of selected {5} ({6:.2f}%)".format(thresh, correct,
                                                                                                    num_paraphrases,
                                                                                                    percent_correct,
                                                                                                            correct,
                                                                                                    parsed,
                                                                                                    percent_of_considered))


def main():
    assert len(sys.argv) == 4
    reader = Seq2SeqDatasetReader(source_tokenizer=NoOpTokenizer(), target_tokenizer=NoOpTokenizer())
    train = reader.read(sys.argv[1])
    val = reader.read(sys.argv[2])
    test = reader.read(sys.argv[3])

    generator = Generator()
    rules, rules_anon, rules_ground, semantics, entities = load_all_2018(generator, GRAMMAR_DIR)
    anonymizer = Anonymizer(*entities)


    neighbors = []
    for x in itertools.chain(train, val):
        command = str(x["source_tokens"][1:-1][0])
        form = str(x["target_tokens"][1:-1][0])
        anon_command = anonymizer(command)
        neighbors.append((anon_command, form))

    test_pairs = []
    for x in test:
        test_pairs.append((str(x["source_tokens"][1:-1][0]), str(x["target_tokens"][1:-1][0])))

    print("Check grammar membership")
    naive_parser = GrammarBasedParser(rules_anon)
    anon_parser = AnonymizingParser(naive_parser, anonymizer)

    correct, parsed = bench_parser(anon_parser, test_pairs)
    print("Got {} of {} ({:.2f})".format(parsed, len(test_pairs), 100.0 * parsed / len(test_pairs)))

    print("Jaccard distance")
    sweep_thresh(neighbors, test_pairs, anonymizer, lambda x, y: jaccard_distance(set(x.split()), set(y.split())),
                 [0.1 * i for i in range(11)])
    print("Edit distance")
    sweep_thresh(neighbors, test_pairs, anonymizer, editdistance.eval)


if __name__ == "__main__":
    main()
