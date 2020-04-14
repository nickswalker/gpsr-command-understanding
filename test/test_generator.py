# coding: utf-8
import os

import unittest

from lark import Tree

from gpsr_command_understanding.generation import generate_sentence_parse_pairs, generate_sentences
from gpsr_command_understanding.generator import Generator
from gpsr_command_understanding.grammar import NonTerminal, ROOT_SYMBOL, tree_printer, ComplexWildCard
from gpsr_command_understanding.loading_helpers import load_all_2018_by_cat, load_all, load_all_2018, GRAMMAR_DIR_2018, \
    GRAMMAR_DIR_2019

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = Generator(grammar_format_version=2018)
        with open(os.path.join(FIXTURE_DIR, "grammar.txt")) as fixture_grammar_file, open(os.path.join(FIXTURE_DIR, "semantics.txt")) as fixture_semantics_file:
            num_rules = self.generator.load_rules(fixture_grammar_file)
            num_semantic_rules = self.generator.load_semantics_rules(fixture_semantics_file)
        self.assertEqual(num_rules, 5)
        self.assertEqual(num_semantic_rules, 3)

    def test_load_2018(self):
        gpsr_2018_by_cat = load_all_2018_by_cat(GRAMMAR_DIR_2018)
        expected_num_rules = [43, 10, 21]
        expected_num_rules_semantics = [32, 107, 42]
        for i, gen in enumerate(gpsr_2018_by_cat):
            rules, semantics = gen.rules, gen.semantics
            self.assertEqual(len(rules), expected_num_rules[i])
            self.assertEqual(len(semantics), expected_num_rules_semantics[i])
        """
        for nonterm, rules in cat[0].items():
            print(nonterm)
            print("")
            for rule in rules:
                print(rule.pretty())
            print("---")
        """
        all_2018 = load_all_2018(GRAMMAR_DIR_2018)
        """
        for nonterm, rules in all_2018.rules.items():
            print(nonterm)
            print("")
            for rule in rules:
                print(rule.pretty())
            print("---")
        """
        self.assertEqual(len(all_2018.rules), 62)
        self.assertEqual(len(all_2018.semantics), 149)


    def test_load_2019_gpsr(self):
        gen = Generator(grammar_format_version=2019)
        load_all(gen, "gpsr", GRAMMAR_DIR_2019)

        rules, semantics = gen.rules, gen.semantics
        self.assertEqual(len(rules), 71)
        self.assertEqual(len(semantics), 0)
        # To manually inspect correctness for now...
        """for nonterm, rules in all_2019[0].items():
            print(nonterm)
            print("")
            for rule in rules:
                print(rule.pretty())
            print("---")"""

    def test_load_2019_egpsr(self):
        gen = Generator(grammar_format_version=2019)
        load_all(gen, "egpsr", GRAMMAR_DIR_2019)

        rules, semantics = gen.rules, gen.semantics
        self.assertEqual(len(rules), 124)
        self.assertEqual(len(semantics), 0)
        # To manually inspect correctness for now...
        """for nonterm, rules in all_2019[0].items():
            print(nonterm)
            print("")
            for rule in rules:
                print(rule.pretty())
            print("---")"""

    def test_generate_pairs(self):
        pairs = list(generate_sentence_parse_pairs(NonTerminal("Main"), self.generator))
        self.assertEqual(len(pairs), 6)

    def test_generate_sentences(self):
        sentences = list(generate_sentences(NonTerminal("Main"), self.generator))
        self.assertEqual(len(sentences), 6)

    def test_generate_all_2018_sentences(self):
        generator = load_all_2018(GRAMMAR_DIR_2018)

        sentences = list(generate_sentences(ROOT_SYMBOL, generator))
        self.assertEqual(len(sentences), 3386)
        unique = set()
        for sentence in sentences:
            count = len(unique)
            unique.add(tree_printer(sentence))
            if len(unique) == count:
                print(tree_printer(sentence))

    def test_generate_pairs_2018(self):
        generator = load_all_2018(GRAMMAR_DIR_2018)
        # If we don't require semantics, the same rules should generate the same number of expansions
        pairs = list(generate_sentence_parse_pairs(ROOT_SYMBOL, generator, yield_requires_semantics=False))
        sentences = list(generate_sentences(ROOT_SYMBOL, generator))
        self.assertEqual(len(pairs), len(sentences))

    def test_ground(self):
        def expr_builder(string):
            return Tree("expression", string.split(" "))
        generator = load_all_2018(GRAMMAR_DIR_2018)

        test_tree = Tree("expression", ["Say", "hi", "to", ComplexWildCard("name", wildcard_id=1), "and", ComplexWildCard("name", wildcard_id=2)])
        expected = expr_builder("Say hi to x and y")
        # FIXME: Setup a mocked knowledgebase
        #self.assertEqual(expected, generator.ground(test_tree))

        # Never repeat
        test_tree = Tree("expression", [ComplexWildCard("name", wildcard_id=1), ComplexWildCard("name", wildcard_id=2)])
        groundings = generator.generate_groundings(test_tree)
        for grounding in groundings:
            first, second = grounding.children
            self.assertNotEqual(first, second)

        test_tree = Tree("expression", [ComplexWildCard("location", wildcard_id=2), "and", ComplexWildCard("name", wildcard_id=2)])
        expected = expr_builder("Say hi to x and y")

