from gpsr_command_understanding.generator.grammar import tree_printer
from gpsr_command_understanding.generator.loading_helpers import load_paired_2018_by_cat, GRAMMAR_DIR_2018
from gpsr_command_understanding.generator.tokens import ROOT_SYMBOL


def main():
    generator = load_paired_2018_by_cat(GRAMMAR_DIR_2018)

    utterance, parse = generator.generate_random(ROOT_SYMBOL, generator)
    print(tree_printer(utterance))


if __name__ == "__main__":
    main()
