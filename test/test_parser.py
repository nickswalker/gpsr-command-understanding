# coding: utf-8
import os
import unittest

from lark import exceptions

from gpsr_semantic_parser.generation import generate_sentences
from gpsr_semantic_parser.generator import Generator
from gpsr_semantic_parser.grammar import tree_printer
from gpsr_semantic_parser.loading_helpers import load_all_2019, \
    load_all_2018
from gpsr_semantic_parser.parser import Parser
from gpsr_semantic_parser.tokens import ROOT_SYMBOL

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
        generator = Generator(grammar_format_version=2018)

        grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2018")
        rules = load_all_2018(generator, grammar_dir)

        sentences = generate_sentences(ROOT_SYMBOL, rules[0])
        parser = Parser(rules[0])
        sentences = set([tree_printer(x) for x in sentences])
        succeeded = 0
        for sentence in sentences:
            try:
                parsed = parser.parse(sentence)
                parsed_pretty = parsed.pretty()
            except exceptions.LarkError as e:
                print(sentence)
                print(e)
                continue
            succeeded += 1

        self.assertEqual(succeeded, len(sentences))


    def test_parse_all_of_2019(self):
        generator = Generator(grammar_format_version=2018)

        grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2019")
        rules = load_all_2019(generator, grammar_dir)

        sentences = generate_sentences(ROOT_SYMBOL, rules[0])
        parser = Parser(rules[0])
        sentences = set([tree_printer(x) for x in sentences])
        succeeded = 0
        for sentence in sentences:

            try:
                parsed = parser.parse(sentence)
                parsed_pretty = parsed.pretty()
            except exceptions.LarkError as e:
                print(sentence)
                print(e)
                continue
            succeeded += 1

        self.assertEqual(succeeded, len(sentences))

