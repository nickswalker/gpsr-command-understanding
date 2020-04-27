#!/usr/bin/env python
import itertools
import sys
import editdistance

from gpsr_command_understanding.generator.grammar import tree_printer
from gpsr_command_understanding.generator.loading_helpers import load_paired_2018, GRAMMAR_DIR_2018
from gpsr_command_understanding.models.noop_tokenizer import NoOpTokenizer
from gpsr_command_understanding.models.seq2seq_data_reader import Seq2SeqDatasetReader
from gpsr_command_understanding.parser import AnonymizingParser, KNearestNeighborParser, GrammarBasedParser
from gpsr_command_understanding.anonymizer import Anonymizer
from nltk.metrics.distance import jaccard_distance


def bench_parser(parser, pairs):
    correct = 0
    parsed = 0
    for utterance, gold in pairs:
        pred = parser(utterance)
        if pred == gold:
            assert(tree_printer(pred) == tree_printer(gold))
            correct += 1
        elif pred:
            pass
            #print(utterance)
            #print(tree_printer(pred))
            #print(tree_printer(gold))
            #print("")
        if pred:
            parsed += 1
        else:
            pass
            # print(utterance)
    return correct, parsed


def sweep_thresh(neighbors, test_pairs, anonymizer, metric, thresh_vals=range(0, 50)):
    num_paraphrases = len(test_pairs)
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
        print("thresh={0:.1f} correct={1}({2:.2f}%) attempted={3}({4:.2f}%) total={5}".format(thresh, correct,
                                                                                                    percent_correct,
                                                                                                    parsed,
                                                                                                    percent_of_considered,
                                                                                              num_paraphrases,))


# FIXME(nickswalker): Why are some of the generated sentences not detected as in-grammar?
def main():
    if not len(sys.argv) == 4:
        print("Pass train, validation and test file paths")
        exit(1)
    reader = Seq2SeqDatasetReader(source_tokenizer=NoOpTokenizer(), target_tokenizer=NoOpTokenizer())
    train = reader.read(sys.argv[1])
    val = reader.read(sys.argv[2])
    test = reader.read(sys.argv[3])

    generator = load_paired_2018(GRAMMAR_DIR_2018)
    anonymizer = Anonymizer.from_knowledge_base(generator.knowledge_base)

    neighbors = []
    for x in itertools.chain(train, val):
        command = str(x["source_tokens"][0])
        form = generator.lambda_parser.parse(str(x["target_tokens"][1:-1][0]))
        anon_command = anonymizer(command)
        neighbors.append((anon_command, form))

    test_pairs = []
    for x in test:
        form = generator.lambda_parser.parse(str(x["target_tokens"][1:-1][0]))
        test_pairs.append((str(x["source_tokens"][0]), form))

    print("Check grammar membership")
    naive_parser = GrammarBasedParser(generator.rules)
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
