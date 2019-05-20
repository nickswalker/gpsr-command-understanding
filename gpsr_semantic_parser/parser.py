import editdistance
import lark
from lark import Transformer, Lark

from gpsr_semantic_parser.tokens import NonTerminal, WildCard

import re


class ToEBNF(Transformer):
    def __default__(self, data, children, meta):
        return " ".join(map(str, children))

    def expression(self, children):
        output = ""
        for child in children:
            if isinstance(child, WildCard):
                if child.name == "void":
                    output += ""
                else:
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
                # Voids are filtered out of input sequences so we can/must ignore these rules
                if child.name == "void":
                    output += ""
                else:
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
    def __init__(self, rules: object) -> object:
        rules = rules
        rch_to_ebnf = ToEBNF()
        as_ebnf = ""
        for non_term, productions in rules.items():
            # TODO: bake this into WildCard and NonTerminal types
            non_term_name = non_term.name.lower()
            if isinstance(non_term, WildCard):
                non_term_name = "wild_"+non_term.to_snake_case()
            line = "!" + non_term_name + ": ("
            for production in productions:
                 line += rch_to_ebnf(production) + "\n\t| "
            line = line[:-4] + " )\n"
            as_ebnf += line
        as_ebnf += """
        %import common.WS
        %ignore WS
"""
        self._parser = Lark(as_ebnf,  start='main')

    def parse(self, utterance):
        try:
            return self._parser.parse(utterance)
        except lark.exceptions.LarkError as e:
            return None

class NearestNeighborParser(object):
    """
    A wrapper class that maps out-of-grammar sentences to their nearest neighbor by edit distance.
    """
    def __init__(self, parser, neighbors):
        self.parser = parser
        self.neighbors = neighbors

    def parse(self, utterance):
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
        return self.parser.parse(nearest)


class Anonymizer(object):
    def __init__(self, objects, categories, names, locations, rooms, gestures):
        self.names = names
        self.categories = categories
        self.locations = locations
        self.rooms = rooms
        self.objects = objects
        self.gestures = gestures
        replacements = {}
        for name in self.names:
            replacements[name] = "{name}"

        for room in self.rooms:
            replacements[room] = "{room}"

        for location in self.locations:
            replacements[location] = "{location}"

        for object in self.objects:
            replacements[object] = "{object}"

        for gesture in self.gestures:
            replacements[gesture] = "{gesture}"

        # use these three lines to do the replacement
        self.rep = dict((re.escape(k), v) for k, v in replacements.items())
        self.pattern = re.compile("|".join(self.rep.keys()))


    def anonymize(self, utterance):
        return self.pattern.sub(lambda m: self.rep[re.escape(m.group(0))], utterance)


class NaiveAnonymizingParser(object):
    def __init__(self, parser, anonymizer):

        self.parser = parser
        self.anonymizer = anonymizer

    def parse(self, utterance):
        return self.parser.parse(self.anonymizer.anonymize(utterance))
