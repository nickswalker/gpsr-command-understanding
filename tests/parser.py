# coding: utf-8
import os
import unittest

from gpsr_semantic_parser.generation import generate_sentence_parse_pairs
from gpsr_semantic_parser.generator import Generator
from gpsr_semantic_parser.grammar import NonTerminal, tree_printer
from gpsr_semantic_parser.loading_helpers import load_all_2018, load_all_2019
from gpsr_semantic_parser.parser import Parser

GRAMMAR_DIR = os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2019")
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
class TestParsers(unittest.TestCase):

    def test_parse_utterance(self):
        rules = {}
        generator = Generator(grammar_format_version=2019)
        grammar = generator.load_rules(os.path.join(FIXTURE_DIR, "grammar.txt"), expand_shorthand=False)
        parser = Parser(grammar)
        test = parser.parse("say hi to him right now please")
        print(test.pretty())
        test = parser.parse("bring it to {pron} now")
        print(test.pretty())

    def test_parse_all_of_2018(self):
        pass

    def test_parse_all_of_2019(self):
        generator = Generator(grammar_format_version=2019)
        all_2019 = load_all_2019(generator, GRAMMAR_DIR, expand_shorthand=False)
        parser = Parser(all_2019[1])
        test = parser.parse("deliver snacks to everyone in the {location}.")
        print(test.pretty())

    def test_parse_choice(self):
        generator = Generator(grammar_format_version=2019)
        test = generator.generator_grammar_parser.parse("$test = ( front | back | main | rear ) $ndoor")
        print(test.pretty())

        test = generator.generator_grammar_parser.parse("$phpeople    = (everyone | all the (people | men | women | guests | elders | children))")

        print(test.pretty())
        print(tree_printer(test))

