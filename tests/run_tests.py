# coding: utf-8
import os
import unittest

from gpsr_semantic_parser.generation import generate_sentence_parse_pairs
from gpsr_semantic_parser.grammar import load_grammar, NonTerminal
from gpsr_semantic_parser.semantics import parse_rule, load_semantics

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
class TestSemanticsLoader(unittest.TestCase):

    def test_parse_rule(self):
        rules = {}
        parse_rule("$vbgopl to the {room 1}, $vbfind (someone | a person), and answer a {question} = say(answer({question}), λ$1:e.(and(person($1), at($1, {room 1}))))", rules)

    def test_expand_shorthand(self):
        pass

    def test_generate(self):
        grammar = load_grammar(os.path.join(FIXTURE_DIR, "grammar.txt"))
        semantics = load_semantics(os.path.join(FIXTURE_DIR, "semantics.txt"))
        pairs = list(generate_sentence_parse_pairs(NonTerminal("Main"),grammar, semantics))
