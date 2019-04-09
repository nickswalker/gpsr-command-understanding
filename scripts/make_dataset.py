import itertools
import os
import random
from os.path import join
import argparse
from collections import defaultdict

from gpsr_semantic_parser.generation import generate_sentences, expand_all_semantics
from gpsr_semantic_parser.semantics import load_semantics
from gpsr_semantic_parser.grammar import prepare_anonymized_rules
from gpsr_semantic_parser.grammar import tree_printer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s","--split", default=[.7,.1,.2], nargs='+', type=float)
    parser.add_argument("-trc","--train-categories", default=[1, 2, 3], nargs='+', type=int)
    parser.add_argument("-tc","--test-categories", default=[1, 2, 3], nargs='+', type=int)
    parser.add_argument("-p","--use-parse-split", action='store_true', default=False)
    parser.add_argument("--name", default=None)
    parser.add_argument("--seed", default=0, required=False)
    parser.add_argument("-i","--incremental-datasets", action='store_true', required=False)
    args = parser.parse_args()

    different_test_dist = False
    if args.test_categories != args.train_categories:
        different_test_dist = True
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

    if not args.name:
        train_cats = "".join([str(x) for x in args.train_categories])
        test_cats = "".join([str(x) for x in args.test_categories])
        args.name = "{}_{}".format(train_cats, test_cats)
        if args.use_parse_split:
            args.name += "_parse"

    pairs_out_path = os.path.join(os.path.abspath(os.path.dirname(__file__) + "/.."), "data", args.name)
    train_out_path = os.path.join(pairs_out_path, "train.txt")
    val_out_path = os.path.join(pairs_out_path, "val.txt")
    test_out_path = os.path.join(pairs_out_path, "test.txt")
    meta_out_path = os.path.join(pairs_out_path, "meta.txt")

    os.mkdir(pairs_out_path)
    
    grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2018")
    common_path = join(grammar_dir, "common_rules.txt")

    cat1_rules = prepare_anonymized_rules(common_path, join(grammar_dir, "gpsr_category_1_grammar.txt"))
    cat2_rules = prepare_anonymized_rules(common_path, join(grammar_dir, "gpsr_category_2_grammar.txt"))
    cat3_rules = prepare_anonymized_rules(common_path, join(grammar_dir, "gpsr_category_3_grammar.txt"))
    cat1_semantics = load_semantics(join(grammar_dir, "gpsr_category_1_semantics.txt"))
    cat2_semantics = load_semantics(
        [join(grammar_dir, "gpsr_category_1_semantics.txt"), join(grammar_dir, "gpsr_category_2_semantics.txt")])
    cat3_semantics = load_semantics(join(grammar_dir, "gpsr_category_3_semantics.txt"))

    # Get utterance -> parse maps
    cat1_pairs = expand_all_semantics(cat1_rules, cat1_semantics)
    cat1_pairs = {tree_printer(utterance): tree_printer(parse) for utterance, parse in cat1_pairs}
    cat2_pairs = expand_all_semantics(cat2_rules, cat2_semantics)
    cat2_pairs = {tree_printer(utterance): tree_printer(parse) for utterance, parse in cat2_pairs}
    cat3_pairs = expand_all_semantics(cat3_rules, cat3_semantics)
    cat3_pairs = {tree_printer(utterance): tree_printer(parse) for utterance, parse in cat3_pairs}

    cat1_unique_utterance_pair = cat1_pairs
    cat1_unique_parse_pair = defaultdict(list)

    for utterance, parse in cat1_pairs.items():
        cat1_unique_parse_pair[parse].append(utterance)

    cat2_unique_utterance_pair = {}
    cat2_unique_parse_pair = defaultdict(list)

    for utterance, parse in cat2_pairs.items():
        # If this utterance was in cat1, then we know that neither the utterance
        # nor the parse are unique (because utterances always produce a unique parse)
        if utterance in cat1_unique_utterance_pair.keys():
            continue
        cat2_unique_utterance_pair[utterance] = parse
        # Even if the utterance is unique, its parse might not be.
        # In that case, we take the parse to "belong to category 1", and tack
        # on this utterance as training data in category 1
        if parse in cat1_unique_parse_pair.keys():
            cat1_unique_parse_pair[parse].append(utterance)
        else:
            # Otherwise, this parse is unique too!
            cat2_unique_parse_pair[parse].append(utterance)

    cat3_unique_utterance_pair = {}
    cat3_unique_parse_pair = defaultdict(list)

    for utterance, parse in cat3_pairs.items():
        if utterance in cat1_pairs.keys() or utterance in cat2_pairs.keys():
            continue
        cat3_unique_utterance_pair[utterance] = parse

        if parse in cat1_unique_parse_pair.keys():
            cat1_unique_parse_pair[parse].append(utterance)
        elif parse in cat2_unique_parse_pair.keys():
            cat2_unique_parse_pair[parse].append(utterance)
        else:
            cat3_unique_parse_pair[parse].append(utterance)

    if args.use_parse_split:
        # Which categories of data do we want
        train_pairs = []
        if 1 in args.train_categories:
            for parse, utterances in cat1_unique_parse_pair.items():
                train_pairs.append((parse, utterances))
        if 2 in args.train_categories:
            for parse, utterances in cat2_unique_parse_pair.items():
                train_pairs.append((parse, utterances))
        if 3 in args.train_categories:
            for parse, utterances in cat3_unique_parse_pair.items():
                train_pairs.append((parse, utterances))

        test_pairs = []
        if 1 in args.test_categories:
            for parse, utterances in cat1_unique_parse_pair.items():
                test_pairs.append((parse, utterances))
        if 2 in args.test_categories:
            for parse, utterances in cat2_unique_parse_pair.items():
                test_pairs.append((parse, utterances))
        if 3 in args.test_categories:
            for parse, utterances in cat3_unique_parse_pair.items():
                test_pairs.append((parse, utterances))
    else:
        train_pairs = []
        if 1 in args.train_categories:
            for utterance, parse in cat1_unique_utterance_pair.items():
                train_pairs.append((utterance, parse))
        if 2 in args.train_categories:
            for utterance, parse in cat2_unique_utterance_pair.items():
                train_pairs.append((utterance, parse))
        if 3 in args.train_categories:
            for utterance, parse in cat3_unique_utterance_pair.items():
                train_pairs.append((utterance, parse))

        test_pairs = []
        if 1 in args.test_categories:
            for utterance, parse in cat1_unique_utterance_pair.items():
                test_pairs.append((utterance, parse))
        if 2 in args.test_categories:
            for utterance, parse in cat2_unique_utterance_pair.items():
                test_pairs.append((utterance, parse))
        if 3 in args.test_categories:
            for utterance, parse in cat3_unique_utterance_pair.items():
                test_pairs.append((utterance, parse))

    # Randomize for the split, but then sort by utterance length before we save out so that things are easier to read
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
        def flatten(original):
            flattened = []
            for parse, utterances in original:
                for utterance in utterances:
                    flattened.append((utterance, parse))
            return flattened
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

    train = sorted(train, key=lambda x: len(x[0]))
    with open(train_out_path, "w") as f:
        for sentence, parse in train:
            f.write(sentence + '\n' + str(parse) + '\n')

    val = sorted(val, key=lambda x: len(x[0]))
    test = sorted(test, key=lambda x: len(x[0]))
    with open(val_out_path, "w") as f:
        for sentence, parse in val:
            f.write(sentence + '\n' + str(parse) + '\n')

    with open(test_out_path, "w") as f:
        for sentence, parse in test:
            f.write(sentence + '\n' + str(parse) + '\n')

    info = "Generated {} dataset with {:.2f}/{:.2f}/{:.2f} split\n".format(args.name, train_percentage, val_percentage, test_percentage)
    info += "train={} val={} test={}".format(len(train), len(val), len(test))
    print(info)
    with open(meta_out_path, "w") as f:
        f.write(info)

if __name__ == "__main__":
    main()
