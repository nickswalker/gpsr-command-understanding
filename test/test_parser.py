# coding: utf-8
import itertools
import os
import random
import unittest

from gpsr_command_understanding.generator.generator import Generator
from gpsr_command_understanding.generator.grammar import tree_printer, DiscardMeta
from gpsr_command_understanding.generator.loading_helpers import load_paired, GRAMMAR_DIR_2018, GRAMMAR_DIR_2019, \
    load_paired_2018, load_2018
from gpsr_command_understanding.generator.paired_generator import PairedGenerator
from gpsr_command_understanding.parser import GrammarBasedParser, AnonymizingParser, KNearestNeighborParser
from gpsr_command_understanding.anonymizer import Anonymizer, NumberingAnonymizer
from gpsr_command_understanding.generator.tokens import ROOT_SYMBOL


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestParsers(unittest.TestCase):

    def test_parse_utterance(self):
        generator = Generator(None, grammar_format_version=2019)
        with open(os.path.join(FIXTURE_DIR, "grammar.txt")) as grammar_file:
            generator.load_rules(grammar_file, expand_shorthand=False)
        parser = GrammarBasedParser(generator.rules)
        test = parser("say hi to him right now please")
        self.assertEqual(7, len(test.children[0].children))
        test = parser("bring it to {pron} now")
        self.assertEqual(5, len(test.children[0].children))

    def test_parse_all_of_2018(self):
        generator = load_2018(GRAMMAR_DIR_2018)

        sentences = generator.generate(ROOT_SYMBOL)
        [generator.extract_metadata(sen) for sen in sentences]
        parser = GrammarBasedParser(generator.rules)
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
        generator = Generator(None, grammar_format_version=2018)

        load_paired(generator, "gpsr", GRAMMAR_DIR_2019)

        sentences = generator.generate(ROOT_SYMBOL)
        [generator.extract_metadata(sen) for sen in sentences]
        parser = GrammarBasedParser(generator.rules)
        sentences = set([tree_printer(x) for x in sentences])
        succeeded = 0
        for sentence in sentences:
            parsed = parser(sentence)
            if parsed:
                succeeded += 1

        self.assertEqual(len(sentences), succeeded)

    def test_nearest_neighbor_parser(self):
        generator = load_2018(GRAMMAR_DIR_2018)

        sentences = generator.generate(ROOT_SYMBOL)
        parser = GrammarBasedParser(generator.rules)
        sentences = list(set([tree_printer(x) for x in sentences]))
        neighbors = [(sentence, parser(sentence)) for sentence in sentences]
        nearest_neighbor_parser = KNearestNeighborParser(neighbors)
        some_sentence = sentences[0]
        tweaked = some_sentence[:-1]
        expected_parse = parser(some_sentence)
        self.assertEqual(expected_parse, nearest_neighbor_parser(some_sentence))
        self.assertEqual(expected_parse, nearest_neighbor_parser(tweaked))

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

    def test_parse_all_2019_ungrounded(self):
        generator = PairedGenerator(None, grammar_format_version=2019)
        load_paired(generator, "gpsr", GRAMMAR_DIR_2019)

        pairs = generator.generate(ROOT_SYMBOL, yield_requires_semantics=False,
                                                  random_generator=random.Random(1))

        [generator.extract_metadata(sentence) for sentence, semantics in pairs]
        parser = GrammarBasedParser(generator.rules)
        # TODO: Finish writing this test
        return

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

        anonymizer = Anonymizer.from_knowledge_base(generator.knowledge_base)
        parser = AnonymizingParser(parser, anonymizer)
        num_tested = 1000
        succeeded = 0
        for tree, parse in itertools.islice(pairs, num_tested):
            sentence = tree_printer(tree)
            parsed = parser(sentence)
            if parsed:
                succeeded += 1
            else:
                print(sentence)
                print(anonymizer(sentence))
                print()
                print(parser(anonymizer(sentence)))

        self.assertEqual(succeeded, num_tested)