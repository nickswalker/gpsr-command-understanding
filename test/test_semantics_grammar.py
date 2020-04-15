# coding: utf-8
import os
import unittest

from gpsr_command_understanding.generator.paired_generator import LambdaParserWrapper

GRAMMAR_DIR_2018 = "gpsr_command_understanding.resources.generator2018"
GRAMMAR_DIR_2019 = "gpsr_command_understanding.resources.generator2019"
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestSemanticsGrammar(unittest.TestCase):

    def setUp(self):
        self.lambda_parser = LambdaParserWrapper()

    def test_parse_wildcard_expression(self):
        test = self.lambda_parser.parse("(test {object} {kobject?} {pron})")
        flattened = [x for x in test.iter_subtrees()]
        self.assertEqual(3, len(flattened))
        self.assertEqual(4, len(test.children[0].children))

    def test_parse_lambda_expression(self):
        test = self.lambda_parser.parse("(test (lambda $1 :e .(yo 1)))")
        flattened = [x.pretty() for x in test.iter_subtrees()]
        self.assertEqual(len(flattened), 8)

    def test_parse_escaped_string(self):
        test = self.lambda_parser.parse("(test \"hello there\" \"second arg with many tokens\")")
        flattened = [x.pretty() for x in test.iter_subtrees()]
        self.assertEqual(3, len(flattened))
