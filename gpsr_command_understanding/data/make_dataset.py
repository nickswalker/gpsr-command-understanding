import copy
import re

from lark import Token

from gpsr_command_understanding.anonymizer import Anonymizer

import itertools
import operator
import os
import random
import argparse
import shutil
from collections import Counter

import lark
import more_itertools

from gpsr_command_understanding.generator.knowledge import AnonymizedKnowledgebase
from gpsr_command_understanding.generator.paired_generator import pairs_without_placeholders
from gpsr_command_understanding.generator.grammar import tree_printer
from gpsr_command_understanding.generator.loading_helpers import GRAMMAR_DIR_2018, load_paired_2018
from gpsr_command_understanding.util import save_data, flatten, merge_dicts, determine_unique_data, \
    replace_child_in_tree

EPS = 0.00001


def validate_args(args):
    if abs(1.0 - sum(args.split)) > 0.00001:
        print("Please ensure split percentages sum to 1")
        exit(1)

    if not (args.anonymized or args.groundings or args.paraphrasings):
        print("Must use at least one of anonymized or grounded pairs")
        exit(1)

    if args.run_anonymizer and not args.paraphrasings:
        print("Can only run anonymizer on paraphrased data")
        exit(1)

    if args.match_logical_split and not args.use_logical_split:
        print("Cannot match form split if not configured to produce form split")
        exit(1)

    if not args.name:
        args.name = ""
        if args.anonymized:
            args.name += "a"
        if args.groundings:
            args.name += "g" + str(args.groundings)
        if args.paraphrasings:
            args.name += "p"
        if args.use_logical_split:
            args.name += "_logical"


def load_data(path, lambda_parser):
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
    parser.add_argument("-s", "--split", default=[.7, .1, .2], nargs='+', type=float)
    parser.add_argument("-l", "--use-logical-split", action='store_true', default=False)
    parser.add_argument("-g", "--groundings", required=False, type=int, default=None)
    parser.add_argument("-a", "--anonymized", required=False, default=False, action="store_true")
    parser.add_argument("-m", "--match-logical-split", required=False, default=None, type=str)
    parser.add_argument("-ra", "--run-anonymizer", required=False, default=False, action="store_true")
    parser.add_argument("-p", "--paraphrasings", required=False, default=None, type=str)
    parser.add_argument("--name", default=None, type=str)
    parser.add_argument("--seed", default=0, required=False, type=int)
    parser.add_argument("-i", "--incremental-datasets", action='store_true', required=False)
    parser.add_argument("-f", "--force-overwrite", action="store_true", required=False, default=False)
    args = parser.parse_args()

    validate_args(args)

    random_source = random.Random(args.seed)

    pairs_out_path = os.path.join(os.path.abspath(os.path.dirname(__file__) + "/../.."), "data", args.name)
    train_out_path, val_out_path, test_out_path, meta_out_path = \
        map(lambda name: os.path.join(pairs_out_path, name + ".txt"), ["train", "val", "test", "meta"])

    if args.force_overwrite and os.path.isdir(pairs_out_path):
        shutil.rmtree(pairs_out_path)

    try:
        os.mkdir(pairs_out_path)
    except FileExistsError as e:
        print("Output path {} already exists. Remove manually if you want to regenerate.".format(pairs_out_path))
        exit(1)
    generator = load_paired_2018(GRAMMAR_DIR_2018)
    lambda_parser = generator.lambda_parser
    pairs = {}

    if args.paraphrasings:
        paraphrasing_pairs = load_data(args.paraphrasings, lambda_parser)
        if args.run_anonymizer:
            anonymizer = Anonymizer.from_knowledge_base(generator.knowledge_base)
            anon_para_pairs = {}
            anon_trigerred = 0
            for command, form in paraphrasing_pairs.items():
                anonymized_command = anonymizer(command)
                if anonymized_command != command:
                    anon_trigerred += 1
                anon_para_pairs[anonymized_command] = form
            paraphrasing_pairs = anon_para_pairs
            print(anon_trigerred, len(paraphrasing_pairs))
        pairs = merge_dicts(pairs, paraphrasing_pairs)

    if args.anonymized or args.groundings:
        gen_pairs = pairs_without_placeholders(generator)
    if args.anonymized:
        old_kb = generator.knowledge_base
        generator.knowledge_base = AnonymizedKnowledgebase()
        anon_pairs = {}
        for utt, logical in gen_pairs.items():
            # The logical form anonymized tokens may not start from zero if the utterance had multiple tokens of the
            # same type. Renumber them.
            utt_grounding_assignment = next(generator.generate_grounding_assignments(utt, ignore_types=True))
            logical_grounding_assignment = next(generator.generate_grounding_assignments(logical, ignore_types=True))
            anon_utt = copy.deepcopy(utt)
            anon_logical = copy.deepcopy(logical)
            for token, replacement in utt_grounding_assignment.items():
                count = replace_child_in_tree(anon_utt, token, replacement)
                assert count > 0
            for token, replacement in logical_grounding_assignment.items():
                count = replace_child_in_tree(anon_logical, token, Token("ESCAPED_STRING", "\"" +replacement + "\""))
                assert count > 0

            if args.groundings:
                # We'll let the next pass of grounding proceed for the utterance
                # It wouldn't make sense to have a grounded logical form and and ungrounded utterance.
                anon_pairs[utt] = anon_logical
            else:
                anon_pairs[anon_utt] = anon_logical
        generator.knowledge_base = old_kb
        pairs = merge_dicts(pairs, anon_pairs)

    if args.groundings:
        grounded_pairs = {}
        for utt, logical in gen_pairs.items():
            groundings = generator.generate_groundings((utt, logical), random_source)
            groundings = itertools.islice(groundings, args.groundings)
            for grounded_utt, grounded_logical in groundings:
                grounded_pairs[grounded_utt] = grounded_logical

        pairs = merge_dicts(pairs, grounded_pairs)

    baked_pairs = {}
    for utt, logical in pairs.items():
        if not isinstance(utt, str):
            baked_pairs[tree_printer(utt)] = tree_printer(logical)
        else:
            baked_pairs[utt] = logical

    by_command, by_form = determine_unique_data(baked_pairs)
    by_command = list(by_command.items())
    by_form = list(by_form.items())
    if args.use_logical_split:
        data_to_split = by_form
    else:
        data_to_split = by_command

    random.Random(args.seed).shuffle(data_to_split)

    # Peg this split to match the split in another dataset. Helpful for making them mergeable while still preserving
    # the no-form-seen-before property of the form split
    if args.match_logical_split:
        train_match = load_data(args.match_logical_split + "/train.txt", lambda_parser)
        train_match = set(train_match.values())
        val_match = load_data(args.match_logical_split + "/val.txt", lambda_parser)
        val_match = set(val_match.values())
        test_match = load_data(args.match_logical_split + "/test.txt", lambda_parser)
        test_match = set(test_match.values())
        train_percentage = len(train_match) / (len(train_match) + len(val_match) + len(test_match))
        val_percentage = len(val_match) / (len(train_match) + len(val_match) + len(test_match))
        test_percentage = len(test_match) / (len(train_match) + len(val_match) + len(test_match))
        train = []
        val = []
        test = []
        for form, commands in by_form:
            target = None
            if form in train_match:
                target = train
            elif form in val_match:
                target = val
            elif form in test_match:
                target = test
            else:
                print(
                    "This logical form doesn't appear in any of the existing data, so we don't know which split to put it in.")
                print(commands[0])
                print(form)
                print("\n")
                #exit(1)
                continue
                # assert False
            target.append((form, commands))
    else:
        train_percentage, val_percentage, test_percentage = args.split
        split1 = int(train_percentage * len(data_to_split))
        split2 = int((train_percentage + val_percentage) * len(data_to_split))
        train, val, test = data_to_split[:split1], data_to_split[split1:split2], data_to_split[split2:]

    # Parse splits would have stored parse-(command list) pairs, so lets
    # flatten out those lists if we need to.
    if args.use_logical_split:
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

    command_vocab = Counter()
    parse_vocab = Counter()
    for command, parse in itertools.chain(train, val, test):
        for token in command.split():
            command_vocab[token] += 1
        for token in parse.split():
            parse_vocab[token] += 1

    info = "Generated {} dataset with {:.2f}/{:.2f}/{:.2f} split\n".format(args.name, train_percentage, val_percentage,
                                                                           test_percentage)
    total_data = len(train) + len(val) + len(test)
    info += "Exact split percentage: {:.2f}/{:.2f}/{:.2f} split\n".format(len(train) / total_data,
                                                                          len(val) / total_data, len(test) / total_data)

    info += "train={} val={} test={}".format(len(train), len(val), len(test))
    print(info)
    with open(meta_out_path, "w") as f:
        f.write(info)

        f.write("\n\nUtterance vocab\n")
        for token, count in sorted(command_vocab.items(), key=operator.itemgetter(1), reverse=True):
            f.write("{} {}\n".format(token, str(count)))

        f.write("\n\nParse vocab\n")
        for token, count in sorted(parse_vocab.items(), key=operator.itemgetter(1), reverse=True):
            f.write("{} {}\n".format(token, str(count)))


if __name__ == "__main__":
    main()
