import os

from gpsr_semantic_parser.generator import Generator
from gpsr_semantic_parser.loading_helpers import load_all_2018
from gpsr_semantic_parser.parser import GrammarBasedParser, NaiveAnonymizingParser, Anonymizer

GRAMMAR_DIR = os.path.abspath(os.path.dirname(__file__) + "/../../resources/generator2018")

def main():
    with open("../../data/2018_paraphrases.txt") as file:
        lines = file.readlines()
        pairs = [(utt, parse) for utt, parse in zip(lines[::2],lines[1::2])]

    num_paraphrases = len(pairs)
    generator = Generator()
    rules, rules_anon, rules_ground, semantics, entities = load_all_2018(generator, GRAMMAR_DIR)
    naive_parser = GrammarBasedParser(rules)
    anonymizer = Anonymizer(*entities)
    anon_parser = NaiveAnonymizingParser(naive_parser, anonymizer)

    naive_parsed = 0
    for utterance, parse in pairs:
        parse = anon_parser.parse(utterance)
        if parse:
            naive_parsed += 1

    print("Parsed {0} out of {1} ({2:.2f}%)".format(naive_parsed, num_paraphrases, 100.0 * float(naive_parsed) / num_paraphrases))


if __name__ == "__main__":
    main()