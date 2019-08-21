# coding: utf-8
import itertools
import os
import random
import unittest

from gpsr_command_understanding.generation import generate_sentences, generate_sentence_parse_pairs
from gpsr_command_understanding.generator import Generator
from gpsr_command_understanding.grammar import tree_printer
from gpsr_command_understanding.loading_helpers import load_all, \
    load_all_2018, load_entities_from_xml
from gpsr_command_understanding.parser import GrammarBasedParser, AnonymizingParser, KNearestNeighborParser
from gpsr_command_understanding.anonymizer import Anonymizer, NumberingAnonymizer
from gpsr_command_understanding.tokens import ROOT_SYMBOL

GRAMMAR_DIR = os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2019")
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
class TestParsers(unittest.TestCase):

    def test_parse_utterance(self):
        generator = Generator(grammar_format_version=2019)
        grammar = generator.load_rules(open(os.path.join(FIXTURE_DIR, "grammar.txt")), expand_shorthand=False)
        parser = GrammarBasedParser(grammar)
        test = parser("say hi to him right now please")
        print(test.pretty())
        test = parser("bring it to {pron} now")
        print(test.pretty())

    def test_parse_all_of_2018(self):
        generator = Generator(grammar_format_version=2018)

        grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2018")
        rules, rules_anon, _, _, _ = load_all_2018(generator, grammar_dir)

        sentences = generate_sentences(ROOT_SYMBOL, rules)
        parser = GrammarBasedParser(rules)
        sentences = set([tree_printer(x) for x in sentences])
        succeeded = 0
        for sentence in sentences:
            parsed = parser(sentence)
            if parsed:
                succeeded += 1
            else:
                print(sentence)

        self.assertEqual(len(sentences), succeeded)

    def test_parse_all_of_2019(self):
        generator = Generator(grammar_format_version=2018)

        grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2019")
        rules, rules_anon, _, _, _ = load_all(generator, grammar_dir)

        sentences = generate_sentences(ROOT_SYMBOL, rules)
        parser = GrammarBasedParser(rules)
        sentences = set([tree_printer(x) for x in sentences])
        succeeded = 0
        for sentence in sentences:
            parsed = parser(sentence)
            if parsed:
                succeeded += 1

        self.assertEqual(len(sentences), succeeded)

    def test_nearest_neighbor_parser(self):
        generator = Generator(grammar_format_version=2018)
        rules = load_all(generator, "gpsr", GRAMMAR_DIR)

        sentences = generate_sentences(ROOT_SYMBOL, rules[0])
        parser = GrammarBasedParser(rules[0])
        sentences = list(set([tree_printer(x) for x in sentences]))
        neighbors = [(sentence, parser(sentence)) for sentence in sentences]
        nearest_neighbor_parser = KNearestNeighborParser(neighbors)
        some_sentence = sentences[0]
        tweaked = some_sentence[:-1]
        expected_parse = parser(some_sentence)
        self.assertEqual(nearest_neighbor_parser(some_sentence), expected_parse)
        self.assertEqual(nearest_neighbor_parser(tweaked), expected_parse)

    def test_anonymizer(self):
        entities = (["ottoman", "apple", "bannana", "chocolates"], ["fruit", "container"],["Bill", "bob"], ["the car", "corridor", "counter"],["corridor"],["counter"],["bedroom", "kitchen", "living room"], ["waving"])
        numbering_anonymizer = NumberingAnonymizer(*entities)
        anonymizer = Anonymizer(*entities)
        no_duplicates = "Bring me the apple from the kitchen and give it to Bill (who is waving) in the corridor"
        self.assertEqual(anonymizer(no_duplicates
                                    ),
                         "Bring me the <object> from the <room> and give it to <name> (who is <gesture>) in the <location>")
        self.assertEqual(anonymizer(no_duplicates), numbering_anonymizer(no_duplicates))
        duplicates = "Bring the apple from the kitchen and put it next to the other apple in the bedroom"
        self.assertEqual(anonymizer(duplicates),
                         "Bring the <object> from the <room> and put it next to the other <object> in the <room>")
        self.assertEqual(
            numbering_anonymizer(duplicates),
            "Bring the <object 1> from the <room 1> and put it next to the other <object 2> in the <room 2>")

    def test_parse_all_2019_anonymized(self):
        generator = Generator(grammar_format_version=2019)

        grammar_dir = os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2019")
        rules, rules_anon, rules_ground, semantics, entities = load_all(generator, grammar_dir)

        sentences = generate_sentence_parse_pairs(ROOT_SYMBOL, rules_ground, {}, yield_requires_semantics=False,
                                                  random_generator=random.Random(1))
        parser = GrammarBasedParser(rules_anon)

        # Bring me the apple from the fridge to the kitchen
        # ---straight anon to clusters--->
        # Bring me the {ob}  from the {loc} to the {loc}
        # ---Grammar based parser--->
        # (Failure; grammar has numbers on locs)

        # Bring me the apple from the fridge to the kitchen
        # ---id naive number anon--->
        # Bring me the {ob}  from the {loc 1} to the {loc 2}
        # ---Grammar based parser--->
        # (Failure; wrong numbers, or maybe)

        anonymizer = Anonymizer(*entities)
        parser = AnonymizingParser(parser, anonymizer)
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