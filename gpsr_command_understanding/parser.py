import operator

from copy import deepcopy

import editdistance
import lark
from lark import Transformer, Lark, Tree

from gpsr_command_understanding.grammar import DiscardVoid
from gpsr_command_understanding.tokens import NonTerminal, WildCard
from gpsr_command_understanding.util import get_wildcards

from queue import PriorityQueue


class ToEBNF(Transformer):
    def __default__(self, data, children, meta):
        return " ".join(map(str, children))

    def expression(self, children):
        output = ""
        for child in children:
            if isinstance(child, WildCard):
                output += " " + "wild_" + child.to_snake_case()
            elif isinstance(child, NonTerminal):
                output += " " + child.name.lower()
            elif isinstance(child, tuple):
                # This is how we smuggle choices up and avoid quoting them
                # like other strings
                output += child[1]
            else:
                output += " \"" + str(child) + "\""
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

    def __init__(self, grammar_rules):
        # We need to destructively modify the rules a bit
        rules = deepcopy(grammar_rules)
        rch_to_ebnf = ToEBNF()
        as_ebnf = ""
        void_remover = DiscardVoid()

        all_wildcard_lhs = [non_term for non_term, _ in rules.items() if isinstance(non_term, WildCard)]
        if len(all_wildcard_lhs) == 0:
            all_rule_trees = [tree for _, trees in rules.items() for tree in trees]
            wildcards = get_wildcards(all_rule_trees)
            for wildcard in wildcards:
                rules[wildcard] = [Tree("expression", [wildcard.to_human_readable()])]
        for non_term, productions in rules.items():
            # TODO: bake this into WildCard and NonTerminal types
            non_term_name = non_term.name.lower()
            if isinstance(non_term, WildCard):
                non_term_name = "wild_"+non_term.to_snake_case()
            line = "!" + non_term_name + ": ("
            for production in productions:
                void_remover.visit(production)
                line += rch_to_ebnf(production) + "\n\t| "

            line = line[:-4] + " )\n"
            as_ebnf += line

        # print(as_ebnf)
        as_ebnf += """
        %import common.WS
        %ignore WS
"""
        self._parser = Lark(as_ebnf,  start='main')

    def __call__(self, utterance):
        try:
            return self._parser.parse(utterance)
        except lark.exceptions.LarkError as e:
            # If you want to see what part didn't fall in the grammar
            # print(e)
            return None


class KNearestNeighborParser(object):
    """
    A wrapper class that maps out-of-grammar sentences to their nearest neighbor by edit distance.
    """

    def __init__(self, neighbors, k=3, distance_threshold=None, confidence_threshold=None, metric=editdistance.eval):
        assert (k > 0)
        self.neighbors = neighbors
        self.distance_threshold = distance_threshold
        self.k = k
        self.metric = metric

    def __call__(self, utterance):
        q = PriorityQueue()
        for neighbor, parse in self.neighbors:
            d = self.metric(neighbor, utterance)
            q.put_nowait((d, (neighbor, parse)))
            if d == 0:
                # Exact match returns the known parse
                return parse

        # Get the top k (lowest distance/priority) and see how they vote
        answer_votes = {}
        for i in range(self.k):
            d, (neighbor, parse) = q.get()
            if d > self.distance_threshold:
                continue
            answer_votes[parse] = answer_votes.get(parse, 0) + 1

        # Reverse to get highest num votes first
        answers_by_num_votes = sorted(answer_votes.items(), key=operator.itemgetter(1), reverse=True)

        # All of our neighbors must've been too far away
        if len(answers_by_num_votes) == 0:
            return None
        return answers_by_num_votes[0][0]


class MappingParser(object):
    """
    Map parser output to some other value specified in a predefined lookup table
    """
    def __init__(self, parser, mapping):
        self.parser = parser
        self.mapping = mapping

    def __call__(self, utterance):
        parse = self.parser(utterance)
        return self.mapping.get(parse, None)


class AnonymizingParser(object):
    """
    Pass input utterances through an anonymizer before parsing
    """
    def __init__(self, parser, anonymizer):

        self.parser = parser
        self.anonymizer = anonymizer

    def __call__(self, utterance):
        return self.parser(self.anonymizer(utterance))
