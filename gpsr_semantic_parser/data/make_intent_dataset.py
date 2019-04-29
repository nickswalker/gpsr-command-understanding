import sys
sys.path.insert(0, "../gpsr-semantic-parser")

import os
import random
import argparse
import shutil

from os.path import join

from gpsr_semantic_parser.generator import Generator
from gpsr_semantic_parser.tokens import NonTerminal, WildCard, Anonymized, ROOT_SYMBOL
from gpsr_semantic_parser.generation import generate_sentences
from gpsr_semantic_parser.util import save_data
from gpsr_semantic_parser.grammar import tree_printer

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

    generator = cmd_gen.rules[0]
    for k,v in generator[3].items():
        print(k)
        print(v)
    cmd_gen.get_utterance_slot_pairs(random_source)

    #grounded_pairs = get_grounding_per_each_parse_by_cat(generator, random_source)
    #print(grounded_pairs[0][0][1].pretty())

    
    #print(len(generator))
    #pairs = [{}]*len(generator)
    #for i in range(args.groundings):
    #    groundings = get_grounding_per_each_parse_by_cat(generator,random_source)
    #    for cat_pairs, groundings in zip(pairs, groundings):
    #        for utt, parse_anon, _ in groundings:
    #            cat_pairs[tree_printer(utt)] = tree_printer(parse_anon)
    #print(pairs[0])
    

if __name__ == "__main__":
    main()
