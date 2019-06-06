from collections import defaultdict

import editdistance
import lark
from lark import Transformer, Lark

from gpsr_semantic_parser.grammar import DiscardVoid, WildcardSimplifier
from gpsr_semantic_parser.tokens import NonTerminal, WildCard

import re


class ToEBNF(Transformer):
    def __default__(self, data, children, meta):
        return " ".join(map(str, children))

    def expression(self, children):
        output = ""
        for child in children:
            if isinstance(child, WildCard):
                output += " \"" + child.to_human_readable() + "\""
            elif isinstance(child, NonTerminal):
                output += " " + child.name.lower()
            elif isinstance(child, tuple):
                # This is how we smuggle choices up and avoid quoting them
                # like other strings
                output += child[1]
            else:
                output += " \"" + str(child) + "\" "
        return output

    def non_terminal(self, children):
        return "{}".format(" ".join(children))

    def choice(self, children):
        output = "("
        for child in children:
            if isinstance(child, WildCard):
                output += " \"" + child.to_human_readable() + "\""
            elif isinstance(child, NonTerminal):
                output += " " + child.name.lower()
            else:
                output += "\"" + child + "\""
            output += " | "
        return ("choice",output[:-3] + ")")

    def rule(self, children):
        return "{}: {}".format(children[0], children[1])

    def constant_placeholder(self, children):
        return "\"" + " ".join(children) + "\""

    def __call__(self,  production):
        return self.transform(production)


class GrammarBasedParser(object):
    """
    Lark-based Earley parser synthesized from the generator grammar.
    "Hard"; only parses things that are exactly in the grammar.
    """
    def __init__(self, rules):
        rules = rules
        rch_to_ebnf = ToEBNF()
        as_ebnf = ""
        void_remover = DiscardVoid()
        wildcard_simplifier = WildcardSimplifier()
        for non_term, productions in rules.items():
            # TODO: bake this into WildCard and NonTerminal types
            non_term_name = non_term.name.lower()
            if isinstance(non_term, WildCard):
                non_term_name = "wild_"+non_term.to_snake_case()
            line = "!" + non_term_name + ": ("
            for production in productions:
                void_remover.visit(production)
                wildcard_simplifier.visit(production)
                line += rch_to_ebnf(production) + "\n\t| "

            line = line[:-4] + " )\n"
            as_ebnf += line
        as_ebnf += """
        %import common.WS
        %ignore WS
"""
        self._parser = Lark(as_ebnf,  start='main')

    def __call__(self, utterance):
        try:
            return self._parser.parse(utterance)
        except lark.exceptions.LarkError as e:
            return None


class NearestNeighborParser(object):
    """
    A wrapper class that maps out-of-grammar sentences to their nearest neighbor by edit distance.
    """
    def __init__(self, parser, neighbors, distance_threshold=20):

        self.parser = parser
        self.neighbors = neighbors
        self.distance_threshold = distance_threshold

    def __call__(self, utterance):
        smallest_distance = 100
        nearest = None
        for i in self.neighbors:
            d = editdistance.eval(i, utterance)
            if d < smallest_distance:
                smallest_distance = d
                nearest = i
            if d == 0:
                break

        if smallest_distance >= 10:
            return None
        return self.parser(nearest)


class Anonymizer(object):
    def __init__(self, objects, categories, names, locations, beacons, placements, rooms, gestures):
        self.names = names
        self.categories = categories
        self.locations = locations
        self.beacons = beacons
        self.placements = placements
        self.rooms = rooms
        self.objects = objects
        self.gestures = gestures
        replacements = {}
        for name in self.names:
            replacements[name] = "name"

        for location in self.locations:
            replacements[location] = "location"


        for room in self.rooms:
            replacements[room] = "location room"

        # Note they're we're explicitly clumping beacons and placements (which may overlap)
        # together to make anonymizing/parsing easier.
        """
        for beacon in self.beacons:
            replacements[beacon] = "location beacon"

        for placement in self.placements:
            replacements[placement] = "location placement"
        """
        for object in self.objects:
            replacements[object] = "object"

        for gesture in self.gestures:
            replacements[gesture] = "gesture"

        for category in self.categories:
            replacements[category] = "category"

        self.rep = replacements
        escaped = dict((re.escape(k), v) for k, v in replacements.items())
        self.pattern = re.compile("\\b(" + "|".join(escaped.keys()) + ")\\b")

    def __call__(self, utterance):
        type_count = defaultdict(lambda: 0)
        scrubbed = utterance
        for match in self.pattern.finditer(utterance):
            type = self.rep[match.group()]
            type_count[type] += 1

        num_type_anon_so_far = defaultdict(lambda: 0)
        while True:
            match = self.pattern.search(scrubbed)
            if not match:
                break
            string = match.groups()[0]
            replacement_type = self.rep[string]
            if type_count[replacement_type] > 1:
                current_num = num_type_anon_so_far[replacement_type] + 1
                replacement_string = "{" + self.rep[string] + " " + str(current_num) + "}"
                num_type_anon_so_far[replacement_type] += 1
            else:
                replacement_string = "{" + self.rep[string] + "}"
            scrubbed = scrubbed.replace(string, replacement_string, 1)

        return scrubbed


class MappingParser(object):
    def __init__(self, parser, mapping):
        self.parser = parser
        self.mapping = mapping

    def parse(self, utterance):
        parse = self.parser.parse(utterance)
        return self.mapping.get(parse, None)


class NaiveAnonymizingParser(object):
    def __init__(self, parser, anonymizer):

        self.parser = parser
        self.anonymizer = anonymizer

    def __call__(self, utterance):
        return self.parser(self.anonymizer(utterance))
