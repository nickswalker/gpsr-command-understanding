#!/usr/bin/env python
import argparse
import json
from operator import itemgetter

import editdistance

from gpsr_command_understanding.generator.grammar import tree_printer
from gpsr_command_understanding.generator.loading_helpers import load_paired_2018, GRAMMAR_DIR_2018
from gpsr_command_understanding.models.noop_tokenizer import NoOpTokenizer
from gpsr_command_understanding.models.seq2seq_data_reader import Seq2SeqDatasetReader
from gpsr_command_understanding.parser import AnonymizingParser, KNearestNeighborParser, GrammarBasedParser
from gpsr_command_understanding.anonymizer import  NumberingAnonymizer
from nltk.metrics.distance import jaccard_distance


def bench_parser(parser, pairs):
    correct = 0
    parsed = 0
    for utterance, gold in pairs:
        pred = parser(utterance)
        if pred == gold:
            assert (tree_printer(pred) == tree_printer(gold))
            correct += 1
        elif pred:
            pass
            # print(utterance)
            # print(tree_printer(pred))
            # print(tree_printer(gold))
            # print("")
        if pred:
            parsed += 1
        else:
            pass
            # print(utterance)
    return correct, parsed


def sweep_thresh(neighbors, test_pairs, anonymizer, metric, thresh_vals=range(0, 50)):
    num_paraphrases = len(test_pairs)
    results = []
    for thresh in thresh_vals:
        anon_edit_distance_parser = KNearestNeighborParser(neighbors, k=1, distance_threshold=thresh, metric=metric)
        anon_edit_distance_parser = AnonymizingParser(anon_edit_distance_parser, anonymizer)
        correct, parsed = bench_parser(anon_edit_distance_parser, test_pairs)

        # Overall accuracy
        percent_correct = 100.0 * float(correct) / num_paraphrases
        # Of those that the parser made a guess on, how many were right
        if parsed == 0:
            percent_of_considered = 0.0
        else:
            percent_of_considered = 100.0 * float(correct) / parsed
        results.append((thresh, percent_correct))
        print("thresh={0:.1f} correct={1}({2:.2f}%) attempted={3}({4:.2f}%) total={5}".format(thresh, correct,
                                                                                              percent_correct,
                                                                                              parsed,
                                                                                              percent_of_considered,
                                                                                              num_paraphrases, ))

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--train", type=str, required=True)
    parser.add_argument("-v", "--val", type=str, required=True)
    parser.add_argument("-te", "--test", type=str, required=True)
    parser.add_argument("-o", "--output-path", type=str)
    args = parser.parse_args()

    reader = Seq2SeqDatasetReader(source_tokenizer=NoOpTokenizer(), target_tokenizer=NoOpTokenizer(),
                                  source_add_start_token=False, source_add_end_token=False)
    train = reader.read(args.train)
    val = reader.read(args.val)
    test = reader.read(args.test)

    generator = load_paired_2018(GRAMMAR_DIR_2018)
    anonymizer = NumberingAnonymizer.from_knowledge_base(generator.knowledge_base)

    train_neighbors = []
    val_neighbors = []
    for x in train:
        command = str(x["source_tokens"][0])
        form = generator.lambda_parser.parse(str(x["target_tokens"][1:-1][0]))
        anon_command = anonymizer(command)
        train_neighbors.append((anon_command, form))

    for x in val:
        command = str(x["source_tokens"][0])
        form = generator.lambda_parser.parse(str(x["target_tokens"][1:-1][0]))
        anon_command = anonymizer(command)
        val_neighbors.append((anon_command, form))

    test_neighbors = []
    for x in test:
        command = str(x["source_tokens"][0])
        form = generator.lambda_parser.parse(str(x["target_tokens"][1:-1][0]))
        anon_command = anonymizer(command)
        test_neighbors.append((anon_command, form))

    train_val_neighbors = train_neighbors + val_neighbors

    print("Check grammar membership")
    naive_parser = GrammarBasedParser(generator.rules)
    anon_parser = AnonymizingParser(naive_parser, anonymizer)

    correct, parsed = bench_parser(anon_parser, test_neighbors)
    grammar_test = 100.0 * parsed / len(test_neighbors)
    print("Got {} of {} ({:.2f})".format(parsed, len(test_neighbors), 100.0 * parsed / len(test_neighbors)))

    print("Jaccard distance")
    jaccard_results = sweep_thresh(train_neighbors, val_neighbors, anonymizer,
                                   lambda x, y: jaccard_distance(set(x.split()), set(y.split())),
                                   [0.1 * i for i in range(11)])
    jaccard_results.sort(key=itemgetter(1))
    best_jaccard_thresh = jaccard_results[-1][0]
    jaccard_test = sweep_thresh(train_val_neighbors, test_neighbors, anonymizer,
                                lambda x, y: jaccard_distance(set(x.split()), set(y.split())), [best_jaccard_thresh])[0]
    print("Jaccard test: ", jaccard_test)
    print("Edit distance")
    edit_results = sweep_thresh(train_neighbors, val_neighbors, anonymizer, editdistance.eval)
    edit_results.sort(key=itemgetter(1))
    best_edit_thresh = edit_results[-1][0]
    edit_test = sweep_thresh(train_val_neighbors, test_neighbors, anonymizer, editdistance.eval, [best_edit_thresh])[0]
    print("Edit test: ", edit_test)
    if args.output_path:
        with open(args.output_path, "w") as out_file:
            json.dump({"grammar": grammar_test, "jaccard_thresh": jaccard_test[0], "jaccard_seq_acc": jaccard_test[1],
                       "edit_thresh": edit_test[0], "edit_seq_acc": edit_test[1]}, out_file)


if __name__ == "__main__":
    main()
