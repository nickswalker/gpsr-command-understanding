import itertools
import operator
import os
import random
import argparse
import shutil
from collections import Counter

import lark
import more_itertools

from gpsr_semantic_parser.generation import pairs_without_placeholders
from gpsr_semantic_parser.generator import Generator, get_grounding_per_each_parse_by_cat
from gpsr_semantic_parser.grammar import tree_printer
from gpsr_semantic_parser.loading_helpers import load_all_2018
from gpsr_semantic_parser.util import determine_unique_cat_data, save_data, flatten, merge_dicts


def validate_args(args):
    if args.test_categories != args.train_categories:
        if len(set(args.test_categories).intersection(set(args.train_categories))) > 0:
            print("Can't have partial overlap of train and test categories")
            exit(1)
        if abs(1.0 - (args.split[0] + args.split[1])) > 0.00001:
            print("Please ensure train and val percentage sum to 1.0 when using different train and test distributions")
            exit(1)
        print("Because train and test distributions are different, using as much of test (100%) as possible")
        args.split[2] = 1
    else:
        if abs(1.0 - sum(args.split)) > 0.00001:
            print("Please ensure split percentages sum to 1")
            exit(1)

    if not (args.anonymized or args.groundings or args.turk):
        print("Must use at least one of anonymized or grounded pairs")

    if not args.name:
        train_cats = "".join([str(x) for x in args.train_categories])
        test_cats = "".join([str(x) for x in args.test_categories])
        args.name = "{}_{}".format(train_cats, test_cats)
        if args.use_parse_split:
            args.name += "_parse"
        if args.anonymized:
            args.name += "_a"
        if args.groundings:
            args.name += "_g" + str(args.groundings)
        if args.turk:
            args.name += "_t"


def get_pairs_by_cats(data, train_categories, test_categories):
    train_pairs = []
    for cat in train_categories:
        # Cats are 1 indexed. Subtract to get 0 indexed
        for pair in data[cat - 1].items():
            train_pairs.append(pair)

    test_pairs = []
    for cat in test_categories:
        # Cats are 1 indexed. Subtract to get 0 indexed
        for pair in data[cat - 1].items():
            test_pairs.append(pair)

    return train_pairs, test_pairs


def load_turk_data(path, lambda_parser):
    pairs = {}
    with open(path) as f:
        line_generator = more_itertools.peekable(enumerate(f))
        while line_generator:
            line_num, line = next(line_generator)
            line = line.strip("\n")
            if len(line) == 0:
                continue

            next_pair = line_generator.peek(None)
            if not next_pair:
                raise RuntimeError()
            next_line_num, next_line = next(line_generator)

            source_sequence, target_sequence = line, next_line

            try:
                pairs[source_sequence] = tree_printer(lambda_parser.parse(target_sequence))
            except lark.exceptions.LarkError:
                print("Skipping malformed parse: {}".format(target_sequence))
    return pairs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s","--split", default=[.7,.1,.2], nargs='+', type=float)
    parser.add_argument("-trc","--train-categories", default=[1, 2, 3], nargs='+', type=int)
    parser.add_argument("-tc","--test-categories", default=[1, 2, 3], nargs='+', type=int)
    parser.add_argument("-p","--use-parse-split", action='store_true', default=False)
    parser.add_argument("-g","--groundings", required=False, type=int, default=None)
    parser.add_argument("-a","--anonymized", required=False, default=True, action="store_true")
    parser.add_argument("-na","--no-anonymized", required=False, dest="anonymized", action="store_false")
    parser.add_argument("-t","--turk", required=False, default=None, type=str)
    parser.add_argument("--name", default=None, type=str)
    parser.add_argument("--seed", default=0, required=False, type=int)
    parser.add_argument("-i","--incremental-datasets", action='store_true', required=False)
    parser.add_argument("-f", "--force-overwrite", action="store_true", required=False, default=False)
    args = parser.parse_args()

    validate_args(args)

    cmd_gen = Generator(grammar_format_version=2018)
    random_source = random.Random(args.seed)

    different_test_dist = False
    if args.test_categories != args.train_categories:
        different_test_dist = True

    pairs_out_path = os.path.join(os.path.abspath(os.path.dirname(__file__) + "/../.."), "data", args.name)
    train_out_path = os.path.join(pairs_out_path, "train.txt")
    val_out_path = os.path.join(pairs_out_path, "val.txt")
    test_out_path = os.path.join(pairs_out_path, "test.txt")
    meta_out_path = os.path.join(pairs_out_path, "meta.txt")

    if args.force_overwrite and os.path.isdir(pairs_out_path):
        shutil.rmtree(pairs_out_path)
    os.mkdir(pairs_out_path)
    
    grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../../resources/generator2018")

    generator = load_all_2018(cmd_gen, grammar_dir)

    pairs = [{}, {}, {}]
    if args.anonymized:
        pairs = [pairs_without_placeholders(rules, semantics) for _, rules, _, semantics in generator]

    # For now this only works with all data
    if args.groundings and len(args.train_categories) == 3:
        for i in range(args.groundings):
            groundings = get_grounding_per_each_parse_by_cat(generator,random_source)
            for cat_pairs, groundings in zip(pairs, groundings):
                for utt, parse_anon, _ in groundings:
                    cat_pairs[tree_printer(utt)] = tree_printer(parse_anon)

    if args.turk and len(args.train_categories) == 3:
        turk_pairs = load_turk_data(args.turk, cmd_gen.lambda_parser)
        pairs[0] = merge_dicts(pairs[0], turk_pairs)

    #pairs_in = [pairs_without_placeholders(rules, semantics, only_in_grammar=True) for _, rules, _, semantics in generator]
    by_utterance, by_parse = determine_unique_cat_data(pairs)

    if args.use_parse_split:
        data_to_split = by_parse
    else:
        data_to_split = by_utterance
    train_pairs, test_pairs = get_pairs_by_cats(data_to_split, args.train_categories, args.test_categories)

    # Randomize for the split, but then sort by utterance length before we save out so that things are easier to read.
    # If these lists are the same, they need to be shuffled the same way...
    random.Random(args.seed).shuffle(train_pairs)
    random.Random(args.seed).shuffle(test_pairs)

    if args.test_categories == args.train_categories:
        # If we're training and testing on the same distributions, these should match exactly
        assert train_pairs == test_pairs

    train_percentage, val_percentage, test_percentage = args.split
    if different_test_dist:
        # Just one split for the first dist, then use all of test
        split1 = int(train_percentage * len(train_pairs))
        train, val, test = train_pairs[:split1], train_pairs[split1:], test_pairs
    else:
        split1 = int(train_percentage * len(train_pairs))
        split2 = int((train_percentage + val_percentage) * len(train_pairs))
        train, val, test = train_pairs[:split1], train_pairs[split1:split2], train_pairs[split2:]

    # Parse splits would have stored parse-(utterance list) pairs, so lets
    # flatten out those lists if we need to.
    if args.use_parse_split:
        train = flatten(train)
        val = flatten(val)
        test = flatten(test)

    # With this switch, we'll simulate getting data one batch at a time
    # so we can assess how quickly we improve
    if args.incremental_datasets:
        limit = 16
        count = 1
        while limit < len(train):
            data_to_write = train[:limit]
            data_to_write = sorted(data_to_write, key=lambda x: len(x[0]))
            with open("".join(train_out_path.split(".")[:-1]) + str(count) + ".txt", "w") as f:
                for sentence, parse in data_to_write:
                    f.write(sentence + '\n' + str(parse) + '\n')
            limit += 16
            count += 1

    save_data(train, train_out_path)
    save_data(val, val_out_path)
    save_data(test, test_out_path)

    utterance_vocab = Counter()
    parse_vocab = Counter()
    for utterance, parse in itertools.chain(train, val, test):
        for token in utterance.split(" "):
            utterance_vocab[token] += 1
        for token in parse.split(" "):
            parse_vocab[token] += 1

    info = "Generated {} dataset with {:.2f}/{:.2f}/{:.2f} split\n".format(args.name, train_percentage, val_percentage, test_percentage)
    total_train_set = len(train) + len(val)
    if different_test_dist:
        total_test_set = len(test)
    else:
        total_train_set += len(test)
        total_test_set = total_train_set
    info += "Exact split percentage: {:.2f}/{:.2f}/{:.2f} split\n".format(len(train)/total_train_set, len(val)/total_train_set, len(test)/total_test_set)

    info += "train={} val={} test={}".format(len(train), len(val), len(test))
    print(info)
    with open(meta_out_path, "w") as f:
        f.write(info)

        f.write("\n\nUtterance vocab\n")
        for token, count in sorted(utterance_vocab.items(), key=operator.itemgetter(1), reverse=True):
            f.write("{} {}\n".format(token, str(count)))

        f.write("\n\nParse vocab\n")
        for token, count in sorted(parse_vocab.items(), key=operator.itemgetter(1), reverse=True):
            f.write("{} {}\n".format(token, str(count)))


if __name__ == "__main__":
    main()
