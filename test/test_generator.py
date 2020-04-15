# coding: utf-8
import os

import unittest

from lark import Tree

from gpsr_command_understanding.generator.generator import Generator
from gpsr_command_understanding.generator.grammar import NonTerminal, ROOT_SYMBOL, tree_printer, ComplexWildCard, \
    DiscardMeta
from gpsr_command_understanding.generator.knowledge import KnowledgeBase
from gpsr_command_understanding.generator.loading_helpers import load_paired_2018_by_cat, \
    GRAMMAR_DIR_2018, \
    GRAMMAR_DIR_2019, load_2018, load

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestGenerator(unittest.TestCase):

    def setUp(self):
        kb = KnowledgeBase({"name": ["n1", "n2", "n3", "n4"]})
        self.generator = Generator(kb, grammar_format_version=2018)
        with open(os.path.join(FIXTURE_DIR, "grammar.txt")) as fixture_grammar_file:
            num_rules = self.generator.load_rules(fixture_grammar_file)
        self.assertEqual(5, num_rules)

    def test_generate_sentences(self):
        sentences = list(self.generator.generate(NonTerminal("Main")))
        self.assertEqual(6, len(sentences))

    def test_generate_all_2018_sentences(self):
        generator = load_2018(GRAMMAR_DIR_2018)

        sentences = list(generator.generate(ROOT_SYMBOL))
        self.assertEqual(3386, len(sentences))
        unique = set()
        for sentence in sentences:
            count = len(unique)
            unique.add(tree_printer(sentence))
            if len(unique) == count:
                print(tree_printer(sentence))

    def test_ground(self):
        def expr_builder(string):
            return Tree("expression", string.split(" "))

        test_tree = Tree("expression", ["Say", "hi", "to", ComplexWildCard("name", wildcard_id=1), "and", ComplexWildCard("name", wildcard_id=2)])
        expected = expr_builder("Say hi to x and y")
        # FIXME: Setup a mocked knowledgebase
        #self.assertEqual(expected, generator.ground(test_tree))

        # Never repeat
        test_tree = Tree("expression", [ComplexWildCard("name", wildcard_id=1), ComplexWildCard("name", wildcard_id=2)])
        groundings = self.generator.generate_groundings(test_tree)
        for grounding in groundings:
            first, second = grounding.children
            self.assertNotEqual(first, second)

        test_tree = Tree("expression", [ComplexWildCard("location", wildcard_id=2), "and", ComplexWildCard("name", wildcard_id=2)])
        expected = expr_builder("Say hi to x and y")

