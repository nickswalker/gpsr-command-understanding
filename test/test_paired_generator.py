# coding: utf-8
import os

import unittest

from lark import Tree, Token

from gpsr_command_understanding.generator.generator import Generator
from gpsr_command_understanding.generator.grammar import NonTerminal, ROOT_SYMBOL, tree_printer, ComplexWildCard
from gpsr_command_understanding.generator.knowledge import KnowledgeBase
from gpsr_command_understanding.generator.loading_helpers import load_paired_2018_by_cat, load_paired, GRAMMAR_DIR_2018, \
    GRAMMAR_DIR_2019, load_paired_2018, load_2018
from gpsr_command_understanding.generator.paired_generator import PairedGenerator

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestPairedGenerator(unittest.TestCase):

    def setUp(self):
        kb = KnowledgeBase({"name": ["n1", "n2", "n3", "n4"]})
        self.generator = PairedGenerator(kb, grammar_format_version=2018)
        with open(os.path.join(FIXTURE_DIR, "grammar.txt")) as fixture_grammar_file, open(os.path.join(FIXTURE_DIR, "semantics.txt")) as fixture_semantics_file:
            num_rules = self.generator.load_rules(fixture_grammar_file)
            num_semantic_rules = self.generator.load_semantics_rules(fixture_semantics_file)
        self.assertEqual(num_rules, 5)
        self.assertEqual(num_semantic_rules, 3)

    def test_load_2018(self):
        gpsr_2018_by_cat = load_paired_2018_by_cat(GRAMMAR_DIR_2018)
        expected_num_rules = [43, 46, 59]
        expected_num_rules_semantics = [32, 107, 42]
        for i, gen in enumerate(gpsr_2018_by_cat):
            rules, semantics = gen.rules, gen.semantics
            self.assertEqual(expected_num_rules[i], len(rules))
            self.assertEqual(expected_num_rules_semantics[i], len(semantics))
        """
        for nonterm, rules in cat[0].items():
            print(nonterm)
            print("")
            for rule in rules:
                print(rule.pretty())
            print("---")
        """
        all_2018 = load_paired_2018(GRAMMAR_DIR_2018)
        """
        for nonterm, rules in all_2018.rules.items():
            print(nonterm)
            print("")
            for rule in rules:
                print(rule.pretty())
            print("---")
        """
        self.assertEqual(62, len(all_2018.rules))
        self.assertEqual(149, len(all_2018.semantics))

    def test_load_2019_gpsr(self):
        gen = PairedGenerator(None, grammar_format_version=2019)
        load_paired(gen, "gpsr", GRAMMAR_DIR_2019)

        rules, semantics = gen.rules, gen.semantics
        self.assertEqual(71, len(rules))
        self.assertEqual(0, len(semantics))
        # To manually inspect correctness for now...
        """for nonterm, rules in all_2019[0].items():
            print(nonterm)
            print("")
            for rule in rules:
                print(rule.pretty())
            print("---")"""

    def test_load_2019_egpsr(self):
        gen = PairedGenerator(None, grammar_format_version=2019)
        load_paired(gen, "egpsr", GRAMMAR_DIR_2019)

        rules, semantics = gen.rules, gen.semantics
        self.assertEqual(124, len(rules))
        self.assertEqual(0, len(semantics))
        # To manually inspect correctness for now...
        """for nonterm, rules in all_2019[0].items():
            print(nonterm)
            print("")
            for rule in rules:
                print(rule.pretty())
            print("---")"""

    def test_generate_pairs(self):
        pairs = list(self.generator.generate(NonTerminal("Main")))
        self.assertEqual(6, len(pairs))

    def test_generate_pairs_2018(self):
        generator = load_2018(GRAMMAR_DIR_2018)
        paired_generator = load_paired_2018(GRAMMAR_DIR_2018)
        # If we don't require semantics, the same rules should generate the same number of expansions
        pairs = list(paired_generator.generate(ROOT_SYMBOL, yield_requires_semantics=False))
        sentences = list(generator.generate(ROOT_SYMBOL))
        self.assertEqual(len(pairs), len(sentences))

    def test_ground(self):
        def expr_builder(string):
            return Tree("expression", string.split(" "))

        test_tree = Tree("expression", ["Say", "hi", "to", ComplexWildCard("name", wildcard_id=1), "and", ComplexWildCard("name", wildcard_id=2)])
        test_sem = Tree("expression", [Tree("greet", [ComplexWildCard("name", wildcard_id=1), ComplexWildCard("name", wildcard_id=2)])])
        expected_utt = expr_builder("Say hi to n1 and n2")
        expected_logical = Tree("expression", [Tree("greet", [Token("ESCAPED_STRING","\"n1\""), Token("ESCAPED_STRING","\"n2\"")])])
        # FIXME: Setup a mocked knowledgebase
        self.assertEqual((expected_utt, expected_logical), self.generator.ground((test_tree, test_sem)))

        # Never repeat
        test_tree = Tree("expression", [ComplexWildCard("name", wildcard_id=1), ComplexWildCard("name", wildcard_id=2)])
        groundings = self.generator.generate_groundings((test_tree, test_tree))
        for ground_utt, ground_logical in groundings:
            first, second = ground_utt.children
            self.assertNotEqual(first, second)

        test_tree = Tree("expression", [ComplexWildCard("location", wildcard_id=2), "and", ComplexWildCard("name", wildcard_id=2)])
        expected = expr_builder("Say hi to x and y")

