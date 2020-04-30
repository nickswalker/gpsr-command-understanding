# coding: utf-8
import os

import unittest
from random import Random

from lark import Tree

from gpsr_command_understanding.generator.generator import Generator
from gpsr_command_understanding.generator.tokens import ROOT_SYMBOL
from gpsr_command_understanding.generator.grammar import NonTerminal, ComplexWildCard
from gpsr_command_understanding.generator.knowledge import KnowledgeBase
from gpsr_command_understanding.generator.loading_helpers import GRAMMAR_DIR_2018, \
    GRAMMAR_DIR_2019, load_2018, load

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestGenerator(unittest.TestCase):

    def setUp(self):
        kb = KnowledgeBase({"name": ["n1", "n2", "n3", "n4"], "location": ["l1", "l2"], "object": ["o1", "o2"]},
                           {"object": {"canPourIn": {"o1": True}}})
        self.generator = Generator(kb, grammar_format_version=2018)
        with open(os.path.join(FIXTURE_DIR, "grammar.txt")) as fixture_grammar_file:
            num_rules = self.generator.load_rules(fixture_grammar_file)
        self.assertEqual(5, num_rules)

    def test_generate_sentences(self):
        sentences = list(self.generator.generate(NonTerminal("Main")))
        self.assertEqual(6, len(sentences))

    def test_generate_all_2018_gpsr_sentences(self):
        generator = load_2018(GRAMMAR_DIR_2018)

        sentences = list(generator.generate(ROOT_SYMBOL))
        self.assertEqual(3386, len(sentences))

        # Pull out all metadata and discard
        [generator.extract_metadata(sen) for sen in sentences]

        # Make sure everything is groundable
        for sentence in sentences:
            grounded = generator.ground(sentence)
            self.assertIsNotNone(grounded)

    def test_generate_all_2019_egpsr_sentences(self):
        generator = Generator(None)
        load(generator, "egpsr", GRAMMAR_DIR_2019)

        # This grammar is too big. Let's get a fixed random sample large enough to use different parts of the grammar
        sentences = list(generator.generate(ROOT_SYMBOL, branch_cap=3, random_generator=Random(0)))
        self.assertEqual(1035, len(sentences))

        # Pull out all metadata and discard
        [generator.extract_metadata(sen) for sen in sentences]

        # Make sure everything is groundable. Should hit a bunch of wildcard conditions
        for sentence in sentences:
            grounded = generator.ground(sentence)
            self.assertIsNotNone(grounded)

    def test_ground(self):
        def expr_builder(string):
            return Tree("expression", string.split(" "))

        test_tree = Tree("expression", ["Say", "hi", "to", ComplexWildCard("name", wildcard_id=1), "and",
                                        ComplexWildCard("name", wildcard_id=2)])
        expected = expr_builder("Say hi to n1 and n2")
        self.assertEqual(expected, self.generator.ground(test_tree))

        # Never repeat
        test_tree = Tree("expression", [ComplexWildCard("name", wildcard_id=1), ComplexWildCard("name", wildcard_id=2)])
        groundings = self.generator.generate_groundings(test_tree)
        for grounding in groundings:
            first, second = grounding.children
            self.assertNotEqual(first, second)

        # ID namespaces are separate
        test_tree = Tree("expression",
                         [ComplexWildCard("location", wildcard_id=2), "and", ComplexWildCard("name", wildcard_id=2)])
        expected = expr_builder("l1 and n1")
        self.assertEqual(expected, self.generator.ground(test_tree))

        # Same ID yields same replacement
        test_tree = Tree("expression",
                         [ComplexWildCard("location", wildcard_id=2), "and", ComplexWildCard("name", wildcard_id=2),
                          "again", ComplexWildCard("name", wildcard_id=2)
                          ])
        expected = expr_builder("l1 and n1 again n1")
        self.assertEqual(expected, self.generator.ground(test_tree))

        # Throw when out of objects
        test_tree = Tree("expression",
                         [ComplexWildCard("location", wildcard_id=1), ComplexWildCard("location", wildcard_id=2),
                          ComplexWildCard("location", wildcard_id=3)
                          ])
        with self.assertRaises(StopIteration):
            self.generator.ground(test_tree)

        # Conditions work
        test_tree = Tree("expression", [ComplexWildCard("object", wildcard_id=1, conditions={"canPourIn": True})
                                        ])
        expected = expr_builder("o1")
        self.assertEqual(expected, self.generator.ground(test_tree))

        # Throw on unknown condition
        test_tree = Tree("expression", [ComplexWildCard("object", wildcard_id=1, conditions={"UNKNOWNCONDITION": True})
                                        ])
        with self.assertRaises(RuntimeError):
            self.generator.ground(test_tree)
