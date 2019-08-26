# coding: utf-8
import os
import sys
import unittest

import importlib_resources

from gpsr_command_understanding.generator import LambdaParserWrapper

GRAMMAR_DIR_2018 = "gpsr_command_understanding.resources.generator2018"
GRAMMAR_DIR_2019 = "gpsr_command_understanding.resources.generator2019"
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestSemanticsGrammar(unittest.TestCase):

    def setUp(self):
        with importlib_resources.path("gpsr_command_understanding.resources", "generator.lark") as path:
            old_main = sys.modules['__main__'].__file__
            sys.modules['__main__'].__file__ = path
            self.lambda_parser = LambdaParserWrapper()

    def test_parse_wildcard_expression(self):
        test = self.lambda_parser.parse("(test {object} {kobject?} {pron})")
        flattened = [x for x in test.iter_subtrees()]
        self.assertEqual(3, len(flattened))
        self.assertEqual(4, len(test.children[0].children))

    def test_parse_lambda_expression(self):
        test = self.lambda_parser.parse("(test (lambda $1 :e .(yo 1)))")
        flattened = [x for x in test.iter_subtrees()]
        self.assertEqual(len(flattened), 7)
