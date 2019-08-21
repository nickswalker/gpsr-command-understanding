# coding: utf-8
import os
import sys
import unittest

import importlib_resources
import lark
from lark import Lark

from gpsr_command_understanding.generation import generate_sentence_parse_pairs
from gpsr_command_understanding.generator import Generator, GENERATOR_GRAMMARS, SEMANTIC_FORMS
from gpsr_command_understanding.grammar import NonTerminal, tree_printer, expand_shorthand, TypeConverter, RemovePrefix
from gpsr_command_understanding.loading_helpers import load_all_2018_by_cat, load_all
from gpsr_command_understanding.parser import GrammarBasedParser

GRAMMAR_DIR_2018 = "gpsr_command_understanding.resources.generator2018"
GRAMMAR_DIR_2019 = "gpsr_command_understanding.resources.generator2019"
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
class TestGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = Generator(grammar_format_version=2019)
        self.rule_parser = Lark(GENERATOR_GRAMMARS[2018],
                                start='rule_start', parser="lalr", transformer=TypeConverter())

    def test_ignore_comment(self):
        comments = ["", "# this is a comment", "; this is a comment", "// this is a comment",
                    '; grammar name Category I', "# test"]
        for comment in comments:
            test = self.rule_parser.parse(comment)
            self.assertEqual(test.children, [])
        test = self.rule_parser.parse("// Ignore this\n $test = But not this")
        self.assertNotEqual(test.children, [])

    def test_parse_rule(self):
        test = self.rule_parser.parse("$test = {pron} went to the mall and {location} $go $home")
        # TODO: Actually check this
        print(test.pretty())

    def test_parse_wildcard_shorthand(self):
        # Check the shorthand wildcards look the same as the full form
        self.assertEqual(self.generator.sequence_parser.parse("{location room}"),
                         self.generator.sequence_parser.parse("{room}"))
        self.assertEqual(self.generator.sequence_parser.parse("{location beacon}"),
                         self.generator.sequence_parser.parse("{beacon}"))
        self.assertEqual(self.generator.sequence_parser.parse("{kobject}"),
                         self.generator.sequence_parser.parse("{object known}"))
        self.assertEqual(self.generator.sequence_parser.parse("{sobject}"),
                         self.generator.sequence_parser.parse("{object special}"))

        # Make sure obfuscation and metadata operators work

    def test_parse_wildcard_ids(self):
        self.assertEqual(self.generator.sequence_parser.parse("{object 1}").children[0].id, 1)
        self.assertEqual(self.generator.sequence_parser.parse("{aobject 1}").children[0].id, 1)
        self.assertEqual(self.generator.sequence_parser.parse("{location 2}").children[0].id, 2)
        self.assertEqual(self.generator.sequence_parser.parse("{name 3}").children[0].id, 3)
        self.assertEqual(self.generator.sequence_parser.parse("{category? 3}").children[0].id, 3)
        self.assertEqual(self.generator.sequence_parser.parse("{category?}").children[0].id, None)

    def test_parse_wildcard_obfuscation(self):
        # Shouldn't be able to obfuscate some types of wildcard
        self.assertRaises(lark.exceptions.UnexpectedCharacters, self.generator.sequence_parser.parse, "{name?")
        self.assertRaises(lark.exceptions.UnexpectedCharacters, self.generator.sequence_parser.parse, "{question?}")

        self.assertEqual(self.generator.sequence_parser.parse("{object?}").children[0].obfuscated, True)
        self.assertEqual(self.generator.sequence_parser.parse("{aobject?}").children[0].obfuscated, True)
        self.assertEqual(self.generator.sequence_parser.parse("{aobject? 1 meta: test}").children[0].obfuscated, True)
        self.assertEqual(self.generator.sequence_parser.parse("{location?}").children[0].obfuscated, True)
        self.assertEqual(self.generator.sequence_parser.parse("{category?}").children[0].obfuscated, True)
        self.assertEqual(self.generator.sequence_parser.parse("{category}").children[0].obfuscated, False)

    def test_parse_wildcard_meta(self):
        parsed_name = self.generator.sequence_parser.parse("{name 1 meta: test}").children[0]
        self.assertEqual(parsed_name.metadata, ["test"])

        # Check meta choice
        meta_choice = '{name meta: {pron sub} is (sitting | standing | lying | waving ) at the {beacon}}'
        parsed = self.generator.sequence_parser.parse(meta_choice).children[0]

    def test_parse_willdcard_integration(self):
        test = self.generator.sequence_parser.parse(
            "Go to the {location placement 1} and get the {kobject}. Then give it to {name 1} who is next to {name 2} at the {location beacon 1} in the {location room}")
        print(test.pretty())

    def test_parse_wildcard_condition(self):
        test = self.generator.sequence_parser.parse("{object where Category=\"test\"}").children[0]
        self.assertEqual(len(test.conditions), 1)
        test = self.generator.sequence_parser.parse("{object where Category=\"test\" and canPour=\"true\"}").children[0]
        self.assertEqual(len(test.conditions), 2)

        # Check boolean conditions

        test = self.generator.sequence_parser.parse("{object where canPourIn=true}").children[0]
        self.assertEqual(1, len(test.conditions))

    def test_parse_pronouns(self):
        pronoun_types = ["pron", "pron obj", "pron sub", "pron pos", "pron paj", "pron posabs", "pron posadj"]
        for type in pronoun_types:
            test = self.generator.sequence_parser.parse(
                "{" + type + "}").children[0]
            self.assertIsNotNone(test)

        # Check shorthands
        pairs = [("pron", "pron obj"), ("pron pos", "pron paj"), ("pron pos", "pron posadj"),
                 ("pron pab", "pron posabs")]
        for first, second in pairs:
            first_wildcard = self.generator.sequence_parser.parse(
                "{" + first + "}").children[0]
            second_wildcard = self.generator.sequence_parser.parse("{" + second + "}").children[0]
            self.assertEqual(first_wildcard, second_wildcard)

    def test_expand_shorthand(self):
        test = self.rule_parser.parse("$test    = top choice | (level one (level two alpha | level two beta))")
        result = expand_shorthand(test)
        self.assertEqual(len(result), 3)

    def test_parse_choice(self):
        # TODO: Add explicit checks here
        test = self.rule_parser.parse("$test = ( oneword | two words)")
        print(test.pretty())
        test = self.rule_parser.parse("$test = ( front | back | main | rear ) $ndoor")
        print(test.pretty())

        top_choice = self.rule_parser.parse("$test = front | back")
        top_choice_short = self.rule_parser.parse("$test = (front | back)")
        self.assertEqual(top_choice, top_choice_short)

        short_mix_choice = self.rule_parser.parse("$test = aa | aa ba")
        print(short_mix_choice.pretty())
        complex_choice = self.rule_parser.parse(
            "$phpeople    = everyone | all the (people | men | women | guests | elders | children)")

        print(complex_choice.pretty())
        print(tree_printer(complex_choice))

    def test_parse_void(self):
        test_rule = '{void meta: The Professional Walker must leave the arena and walk through a crowd of at least 5 people, say "$whattosay", find a t-shirt, the Professional Walker must lead the robot to {room 2} }'
        test = self.generator.sequence_parser.parse(test_rule)
        self.assertEqual(len(test.children), 1)
        self.assertEqual(len(test.children[0].metadata), 36)

    def test_generate(self):
        generator = Generator(grammar_format_version=2018)
        grammar = generator.load_rules(open(os.path.join(FIXTURE_DIR, "grammar.txt")))
        semantics = generator.load_semantics_rules(open(os.path.join(FIXTURE_DIR, "semantics.txt")))
        pairs = list(generate_sentence_parse_pairs(NonTerminal("Main"),grammar, semantics))
        self.assertEqual(len(pairs), 6)

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
        all_2019_gpsr = load_all(generator, "gpsr", GRAMMAR_DIR_2019, expand_shorthand=False)
        all_2019_eegpsr = load_all(generator, "eegpsr", GRAMMAR_DIR_2019, expand_shorthand=False)
        # To manually inspect correctness for now...
        """for nonterm, rules in all_2019[0].items():
            print(nonterm)
            print("")
            for rule in rules:
                print(rule.pretty())
            print("---")"""
