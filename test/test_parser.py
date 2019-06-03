# coding: utf-8
import itertools
import os
import random
import unittest

from lark import exceptions

from gpsr_semantic_parser.generation import generate_sentences, generate_sentence_parse_pairs
from gpsr_semantic_parser.generator import Generator
from gpsr_semantic_parser.grammar import tree_printer
from gpsr_semantic_parser.loading_helpers import load_all_2019, \
    load_all_2018, load_entities_from_xml
from gpsr_semantic_parser.parser import GrammarBasedParser, NearestNeighborParser, Anonymizer, NaiveAnonymizingParser
from gpsr_semantic_parser.tokens import ROOT_SYMBOL

GRAMMAR_DIR = os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2019")
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
class TestParsers(unittest.TestCase):

    def test_parse_utterance(self):
        rules = {}
        generator = Generator(grammar_format_version=2019)
        grammar = generator.load_rules(os.path.join(FIXTURE_DIR, "grammar.txt"), expand_shorthand=False)
        parser = GrammarBasedParser(grammar)
        test = parser("say hi to him right now please")
        print(test.pretty())
        test = parser("bring it to {pron} now")
        print(test.pretty())

    def test_parse_all_of_2018(self):
        generator = Generator(grammar_format_version=2018)

        grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2018")
        rules = load_all_2018(generator, grammar_dir)

        sentences = generate_sentences(ROOT_SYMBOL, rules[0])
        parser = GrammarBasedParser(rules[0])
        sentences = set([tree_printer(x) for x in sentences])
        succeeded = 0
        for sentence in sentences:
            parsed = parser(sentence)
            if parsed:
                succeeded += 1

        self.assertEqual(len(sentences), succeeded)

    def test_parse_all_of_2019(self):
        generator = Generator(grammar_format_version=2018)

        grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2019")
        rules = load_all_2019(generator, grammar_dir)

        sentences = generate_sentences(ROOT_SYMBOL, rules[0])
        parser = GrammarBasedParser(rules[0])
        sentences = set([tree_printer(x) for x in sentences])
        succeeded = 0
        for sentence in sentences:
            parsed = parser(sentence)
            if parsed:
                succeeded += 1

        self.assertEqual(len(sentences), succeeded)

    def test_nearest_neighbor_parser(self):
        generator = Generator(grammar_format_version=2018)
        rules = load_all_2019(generator, GRAMMAR_DIR)

        sentences = generate_sentences(ROOT_SYMBOL, rules[0])
        parser = GrammarBasedParser(rules[0])
        sentences = list(set([tree_printer(x) for x in sentences]))
        nearest_neighbor_parser = NearestNeighborParser(parser, sentences)
        some_sentence = sentences[0]
        tweaked = some_sentence[:-1]
        expected_parse = parser(some_sentence)
        self.assertEqual(nearest_neighbor_parser(some_sentence), expected_parse)
        self.assertEqual(nearest_neighbor_parser(tweaked), expected_parse)

    def test_anonymizer(self):
        entities = (["ottoman", "apple", "bannana", "chocolates"], ["fruit", "container"],["Bill", "bob"], ["the car", "corridor", "counter"],["corridor"],["counter"],["bedroom", "kitchen", "living room"], ["waving"])
        anonymizer = Anonymizer(*entities)
        self.assertEqual("Bring me the {object} from the {location room} and give it to {name} (who is {gesture}) in the {location}", anonymizer("Bring me the apple from the kitchen and give it to Bill (who is waving) in the corridor"))

    def test_parse_all_2019_anonymized(self):
        generator = Generator(grammar_format_version=2019)

        grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2019")
        rules = load_all_2019(generator, grammar_dir)

        sentences = generate_sentence_parse_pairs(ROOT_SYMBOL, rules[2], {},yield_requires_semantics=False,random_generator=random.Random(1))
        parser = GrammarBasedParser(rules[0])

        anonymizer = Anonymizer(*rules[-1])
        parser = NaiveAnonymizingParser(parser, anonymizer)
        num_tested = 1000
        succeeded = 0
        for sentence, parse in itertools.islice(sentences, num_tested):
            sentence = tree_printer(sentence)
            parsed = parser(sentence)
            if parsed:
                succeeded += 1
            else:
                print(sentence)
                print(anonymizer(sentence))
                print()
                print(parser(anonymizer(sentence)))

        self.assertEqual(succeeded, num_tested)