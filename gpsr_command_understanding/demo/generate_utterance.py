import sys
import random

from gpsr_command_understanding.generator.generator import Generator
from gpsr_command_understanding.generator.grammar import tree_printer
from gpsr_command_understanding.generator.loading_helpers import load, GRAMMAR_YEAR_TO_MODULE
from gpsr_command_understanding.generator.tokens import ROOT_SYMBOL
from lark.tree import Tree


def main():
    year = int(sys.argv[1])
    gen = Generator(None, year)
    load(gen, "gpsr", GRAMMAR_YEAR_TO_MODULE[year])

    utterance = gen.generate_random(ROOT_SYMBOL, random_generator=random.Random(11))
    utterance, meta = gen.extract_metadata(utterance)
    grounded = gen.ground(utterance)
    print(tree_printer(grounded))

    print(tree_printer(utterance))
    for _, note in meta.items():
        if note:
            print("\t" + tree_printer(Tree("expression", note)))


if __name__ == "__main__":
    main()
