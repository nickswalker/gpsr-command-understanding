import sys
sys.path.insert(0, "../gpsr-semantic-parser")

import itertools
import operator
import os
import random
import argparse
import shutil

from os.path import join
from lark import lark, Tree, Token
from collections import Counter
import more_itertools

from gpsr_semantic_parser.generator import Generator
from gpsr_semantic_parser.tokens import NonTerminal, WildCard, Anonymized, ROOT_SYMBOL
from gpsr_semantic_parser.generation import generate_sentences
from gpsr_semantic_parser.util import determine_unique_cat_data, save_slot_data, flatten, get_pairs_by_cats, merge_dicts
from gpsr_semantic_parser.grammar import tree_printer

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

    if not args.name:
        train_cats = "".join([str(x) for x in args.train_categories])
        test_cats = "".join([str(x) for x in args.test_categories])
        args.name = "{}_{}".format(train_cats, test_cats)

    if args.use_parse_split:
        args.name += "_parse"
    if args.turk:
        args.name += "_t"


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
    parser.add_argument("-b","--branch-cap", default=None, type=int)
    parser.add_argument("-t","--turk", required=False, default=None, type=str)
    parser.add_argument("--name", default=None, type=str)
    parser.add_argument("--seed", default=0, required=False, type=int)
    parser.add_argument("-f", "--force-overwrite", action="store_true", required=False, default=False)
    args = parser.parse_args()

    validate_args(args)
    
    cmd_gen = Generator(grammar_format_version=2018, semantic_form_version="slot")
    #cmd_gen = Generator(grammar_format_version=2018, semantic_form_version="lambda")
    random_source = random.Random(args.seed)

    pairs_out_path = os.path.join(os.path.abspath(os.path.dirname(__file__) + "/../.."), "data", args.name)
    train_out_path = os.path.join(pairs_out_path, "train.txt")
    val_out_path = os.path.join(pairs_out_path, "val.txt")
    test_out_path = os.path.join(pairs_out_path, "test.txt")
    meta_out_path = os.path.join(pairs_out_path, "meta.txt")

    if args.force_overwrite and os.path.isdir(pairs_out_path):
        shutil.rmtree(pairs_out_path)
    os.mkdir(pairs_out_path)

    grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../../resources/generator2018")
    common_path = join(grammar_dir, "common_rules.txt")
    paths = tuple(map(lambda x: join(grammar_dir, x), ["objects.xml", "locations.xml", "names.xml", "gestures.xml"]))
    grammar_file_paths = [common_path, join(grammar_dir, "gpsr_category_1_grammar.txt")]
    semantics_file_paths = [join(grammar_dir, "gpsr_category_1_slot.txt"), join(grammar_dir, "common_rules_slot.txt")]

    cmd_gen.load_set_of_rules(grammar_file_paths, semantics_file_paths, *paths)

    grammar_file_paths = [common_path, join(grammar_dir, "gpsr_category_2_grammar.txt")]
    semantics_file_paths = [join(grammar_dir, "gpsr_category_2_slot.txt"), join(grammar_dir, "common_rules_slot.txt")]

    cmd_gen.load_set_of_rules(grammar_file_paths, semantics_file_paths, *paths)

    grammar_file_paths = [common_path, join(grammar_dir, "gpsr_category_3_grammar.txt")]
    semantics_file_paths = [join(grammar_dir, "gpsr_category_3_slot.txt"), join(grammar_dir, "common_rules_slot.txt")]

    cmd_gen.load_set_of_rules(grammar_file_paths, semantics_file_paths, *paths)

    #generator = cmd_gen.rules[2]
    #for k,v in generator[2].items():
    #    print(k)
    #    print(v)
    #    print("-------------------------------------------------------------------")

    pairs = []
    pairs.append(cmd_gen.get_utterance_semantics_pairs(random_source, [1], args.branch_cap))
    pairs.append(cmd_gen.get_utterance_semantics_pairs(random_source, [2], args.branch_cap))
    pairs.append(cmd_gen.get_utterance_semantics_pairs(random_source, [3], args.branch_cap))
    #pairs = [cmd_gen.get_utterance_semantics_pairs(random_source, [cat], args.branch_cap) for cat in [1, 2, 3]]

    #if args.turk and len(args.train_categories) == 3:
    #    turk_pairs = load_turk_data(args.turk, cmd_gen.lambda_parser)
    #    pairs[0] = merge_dicts(pairs[0], turk_pairs)

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

    different_test_dist = False
    if args.test_categories != args.train_categories:
        different_test_dist = True

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

    save_slot_data(train, train_out_path)
    save_slot_data(val, val_out_path)
    save_slot_data(test, test_out_path)

    utterance_vocab = Counter()
    parse_vocab = Counter()
    for utterance, parse in itertools.chain(train, val, test):
        for token in utterance.split(" "):
            utterance_vocab[token] += 1
        for token in parse.split(" "):
            parse_vocab[token] += 1

    info = "Generated {} dataset with {:.2f}/{:.2f}/{:.2f} split\n".format(args.name, train_percentage, val_percentage, test_percentage)
    total = len(train) + len(val) + len(test)
    info += "Exact split percentage: {:.2f}/{:.2f}/{:.2f} split\n".format(len(train)/total, len(val)/total, len(test)/total)

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
