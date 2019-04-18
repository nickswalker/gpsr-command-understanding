# coding: utf-8
import os
import unittest

from gpsr_semantic_parser.generation import generate_sentence_parse_pairs
from gpsr_semantic_parser.generator import Generator
from gpsr_semantic_parser.grammar import NonTerminal, tree_printer

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
class TestSemanticsLoader(unittest.TestCase):

    def test_parse_rule(self):

        rules = {}
        test = lambda_parser.parse("(test (lambda $1 :e .(yo 1)))")
        print(test.pretty())
        #parse_rule("$vbgopl to the {room 1}, $vbfind (someone | a person), and answer a {question} = (say (answer {question}) (lambda $1:e (person $1) (at $1 {room 1})))", rules)

    def test_parse_choice(self):
        generator = Generator(grammar_format_version=2019)
        test = generator.generator_grammar_parser.parse("$test = ( front | back | main | rear ) $ndoor")
        print(test.pretty())

        test = generator.generator_grammar_parser.parse("$phpeople    = (everyone | all the (people | men | women | guests | elders | children))")
        print(test.pretty())
        print(tree_printer(test))

    def test_expand_shorthand(self):
        pass

    def test_generate(self):
        generator = Generator(grammar_format_version=2018)
        grammar = generator.load_rules(os.path.join(FIXTURE_DIR, "grammar.txt"))
        semantics = generator.load_rules(os.path.join(FIXTURE_DIR, "semantics.txt"))
        pairs = list(generate_sentence_parse_pairs(NonTerminal("Main"),grammar, semantics))
