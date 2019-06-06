# coding: utf-8
import os
import unittest

from gpsr_command_understanding.generation import generate_sentence_parse_pairs
from gpsr_command_understanding.generator import Generator
from gpsr_command_understanding.grammar import NonTerminal, tree_printer, expand_shorthand
from gpsr_command_understanding.loading_helpers import load_all_2018_by_cat, load_all_2019
from gpsr_command_understanding.parser import GrammarBasedParser

GRAMMAR_DIR_2018 = os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2018")
GRAMMAR_DIR_2019 = os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2019")
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
class TestGenerator(unittest.TestCase):

    def setUp(self) -> None:
        self.generator = Generator(grammar_format_version=2019)

    def test_parse_rule(self):
        rules = {}
        test = self.generator.lambda_parser.parse("(test (lambda $1 :e .(yo 1)))")
        print(test.pretty())
        #parse_rule("$vbgopl to the {room 1}, $vbfind (someone | a person), and answer a {question} = (say (answer {question}) (lambda $1:e (person $1) (at $1 {room 1})))", rules)

    def test_parse_basic(self):
        test = self.generator.generator_grammar_parser.parse("$test = {pron} went to the mall and {location} $go $home")
        print(test.pretty())

    def test_parse_wildcards(self):
        test = self.generator.generator_sequence_parser.parse(
            "Go to the {location placement 1} and get the {kobject}. Then give it to {name 1} who is next to {name 2} at the {location beacon 1} in the {location room}")
        print(test.pretty())

    def test_expand_shorthand(self):
        test = self.generator.generator_grammar_parser.parse("$test    = top choice | (level one (level two alpha | level two beta))")
        result = expand_shorthand(test)
        self.assertEqual(len(result), 3)

    def test_parse_choice(self):
        test = self.generator.generator_grammar_parser.parse("$test = ( oneword | two words)")
        print(test.pretty())
        test = self.generator.generator_grammar_parser.parse("$test = ( front | back | main | rear ) $ndoor")
        print(test.pretty())


        top_choice = self.generator.generator_grammar_parser.parse("$test = front | back")
        top_choice_short = self.generator.generator_grammar_parser.parse("$test = (front | back)")
        self.assertEqual(top_choice, top_choice_short)

        short_mix_choice = self.generator.generator_grammar_parser.parse("$test = aa | aa ba")
        print(short_mix_choice.pretty())
        complex_choice = self.generator.generator_grammar_parser.parse("$phpeople    = everyone | all the (people | men | women | guests | elders | children)")

        print(complex_choice.pretty())
        print(tree_printer(complex_choice))

    def test_generate(self):
        generator = Generator(grammar_format_version=2018)
        grammar = generator.load_rules(os.path.join(FIXTURE_DIR, "grammar.txt"))
        semantics = generator.load_rules(os.path.join(FIXTURE_DIR, "semantics.txt"))
        pairs = list(generate_sentence_parse_pairs(NonTerminal("Main"),grammar, semantics))

    def test_load_2018(self):
        generator = Generator(grammar_format_version=2018)
        all_2018= load_all_2018_by_cat(generator, GRAMMAR_DIR_2018, expand_shorthand=False)
        # To manually inspect correctness for now...
        """for nonterm, rules in all_2018[0].items():
            print(nonterm)
            print("")
            for rule in rules:
                print(rule.pretty())
            print("---")"""

    def test_load_2019(self):
        generator = Generator(grammar_format_version=2019)
        all_2019 = load_all_2019(generator, GRAMMAR_DIR_2019, expand_shorthand=False)

        # To manually inspect correctness for now...
        """for nonterm, rules in all_2019[0].items():
            print(nonterm)
            print("")
            for rule in rules:
                print(rule.pretty())
            print("---")"""
