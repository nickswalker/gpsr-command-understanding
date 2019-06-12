import copy
import os

from gpsr_command_understanding.generation import generate_sentences, generate_sentence_parse_pairs, \
    expand_all_semantics
from gpsr_command_understanding.generator import Generator
from gpsr_command_understanding.grammar import tree_printer, rule_dict_to_str
from gpsr_command_understanding.loading_helpers import load_all_2018, load_all_2018_by_cat
from gpsr_command_understanding.parser import GrammarBasedParser, AnonymizingParser, NearestNeighborParser, \
    MappingParser
from gpsr_command_understanding.anonymizer import Anonymizer
from gpsr_command_understanding.tokens import ROOT_SYMBOL
from gpsr_command_understanding.util import has_placeholders

GRAMMAR_DIR = os.path.abspath(os.path.dirname(__file__) + "/../../resources/generator2018")


def bench_parser(parser, pairs):
    parsed = 0
    for utterance, gold in pairs:
        pred = parser(utterance)
        if pred == gold:
            parsed += 1
    return parsed


def main():
    with open("../../data/2018_paraphrases.txt") as file:
        lines = file.readlines()
        paraphrase_pairs = [(utt.strip(), parse.strip()) for utt, parse in zip(lines[::2], lines[1::2])]

    num_paraphrases = len(paraphrase_pairs)
    generator = Generator()
    rules, rules_anon, rules_ground, semantics, entities = load_all_2018(generator, GRAMMAR_DIR)
    naive_parser = GrammarBasedParser(rules_anon)
    anonymizer = Anonymizer(*entities)
    generator = Generator()
    generator = load_all_2018_by_cat(generator, GRAMMAR_DIR)

    # TODO: Make sure these can run through as well
    # cat_sentences = [set(generate_sentences(ROOT_SYMBOL, rules_anon)) for _,rules_anon, _, _ in generator]
    # all_sentences = set().union(*cat_sentences)
    pairs = {}
    for _, rules_anon, _, semantics in generator:
        for utterance, parse in expand_all_semantics(rules_anon, semantics):
            # Happens sometimes due to object known not being expanded in cat 1
            if has_placeholders(utterance):
                continue
            pairs[utterance] = parse
    pairs = [(tree_printer(sentence), tree_printer(parse)) for sentence, parse in pairs.items()]
    sentences = [sentence for sentence, _ in pairs]

    ########## Check with no editdistance
    anon_parser = AnonymizingParser(naive_parser, anonymizer)

    """utterance_none_pairs = [(utt, None) for utt, _ in paraphrase_pairs]
    parsed = bench_parser(anon_parser, utterance_none_pairs)
    parsed = num_paraphrases - parsed

    print("{0} out of {1} fall in grammar ({2:.2f}%)".format(parsed, num_paraphrases, 100.0 * float(parsed) / num_paraphrases))"""
    ##################

    mapping = {}
    # Get a mapping from grammar parses to semantic forms
    for sentence, form in pairs:
        parse = naive_parser(sentence)
        if not parse:
            print(sentence)
            continue
        mapping[parse] = form
    print(len(pairs))

    for i in range(0, 50):
        anon_edit_distance_parser = NearestNeighborParser(anon_parser, sentences, distance_threshold=i)
        anon_edit_distance_parser = MappingParser(anon_edit_distance_parser, mapping)
        anon_edit_distance_parser = AnonymizingParser(anon_edit_distance_parser, anonymizer)
        parsed = bench_parser(anon_edit_distance_parser, paraphrase_pairs)
        print("i={0} Parsed {1} out of {2} correctly ({3:.2f}%)".format(i, parsed, num_paraphrases,
                                                                        100.0 * float(parsed) / num_paraphrases))


if __name__ == "__main__":
    main()
