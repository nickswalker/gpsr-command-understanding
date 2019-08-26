# coding: utf-8
import os
import sys
import unittest

import importlib_resources
import lark
from lark import Lark

from gpsr_command_understanding.generation import generate_sentence_parse_pairs, generate_sentences
from gpsr_command_understanding.generator import Generator, GENERATOR_GRAMMARS, SEMANTIC_FORMS
from gpsr_command_understanding.grammar import NonTerminal, tree_printer, expand_shorthand, TypeConverter, RemovePrefix
from gpsr_command_understanding.loading_helpers import load_all_2018_by_cat, load_all
from gpsr_command_understanding.parser import GrammarBasedParser

GRAMMAR_DIR_2018 = "gpsr_command_understanding.resources.generator2018"
GRAMMAR_DIR_2019 = "gpsr_command_understanding.resources.generator2019"
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
class TestGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = Generator(grammar_format_version=2018)
        grammar = self.generator.load_rules(open(os.path.join(FIXTURE_DIR, "grammar.txt")))
        semantics = self.generator.load_semantics_rules(open(os.path.join(FIXTURE_DIR, "semantics.txt")))

    def test_load_2018(self):
        generator = Generator(grammar_format_version=2018)
        all_2018 = load_all_2018_by_cat(generator, GRAMMAR_DIR_2018)
        expected_num_rules = [43, 10, 21]
        expected_num_rules_semantics = [0, 0, 0]
        for i, cat in enumerate(all_2018):
            rules, semantics = cat
            self.assertEqual(len(rules), expected_num_rules[i])
        """
        for nonterm, rules in cat[0].items():
            print(nonterm)
            print("")
            for rule in rules:
                print(rule.pretty())
            print("---")
        """

    def test_load_2019(self):
        generator = Generator(grammar_format_version=2019)
        all_2019_gpsr = load_all(generator, "gpsr", GRAMMAR_DIR_2019)
        all_2019_eegpsr = load_all(generator, "eegpsr", GRAMMAR_DIR_2019)
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
