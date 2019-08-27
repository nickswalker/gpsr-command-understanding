# coding: utf-8
import os

import unittest


from gpsr_command_understanding.generation import generate_sentence_parse_pairs, generate_sentences
from gpsr_command_understanding.generator import Generator
from gpsr_command_understanding.grammar import NonTerminal
from gpsr_command_understanding.loading_helpers import load_all_2018_by_cat, load_all

GRAMMAR_DIR_2018 = "gpsr_command_understanding.resources.generator2018"
GRAMMAR_DIR_2019 = "gpsr_command_understanding.resources.generator2019"
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = Generator(grammar_format_version=2018)
        num_rules = self.generator.load_rules(open(os.path.join(FIXTURE_DIR, "grammar.txt")))
        num_semantic_rules = self.generator.load_semantics_rules(open(os.path.join(FIXTURE_DIR, "semantics.txt")))
        self.assertEqual(num_rules, 5)
        self.assertEqual(num_semantic_rules, 3)

    def test_load_2018(self):
        all_2018 = load_all_2018_by_cat(GRAMMAR_DIR_2018)
        expected_num_rules = [43, 10, 21]
        expected_num_rules_semantics = [32, 107, 42]
        for i, gen in enumerate(all_2018):
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
