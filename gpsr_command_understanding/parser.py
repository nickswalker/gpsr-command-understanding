import operator

from copy import deepcopy
from itertools import count

import editdistance
import lark
from lark import Transformer, Lark, Tree

from gpsr_command_understanding.generator.generator import Generator
from gpsr_command_understanding.generator.grammar import DiscardVoid, DiscardMeta
from gpsr_command_understanding.generator.knowledge import AnonymizedKnowledgebase
from gpsr_command_understanding.generator.tokens import NonTerminal, WildCard
from gpsr_command_understanding.util import get_wildcards_forest

from queue import PriorityQueue


class ToEBNF(Transformer):
    def __default__(self, data, children, meta):
        return " ".join(map(str, children))

    def expression(self, children):
        output = ""
        for child in children:
            if isinstance(child, WildCard):
                output += " " + "wild_" + child.to_snake_case().replace("?", "obf")
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
        return ("choice", output[:-3] + ")")

    def rule(self, children):
        return "{}: {}".format(children[0], children[1])

    def constant_placeholder(self, children):
        return "\"" + " ".join(children) + "\""

    def __call__(self, production):
        return self.transform(production)


def expr_builder(item):
    return Tree("expression", [item])


class GrammarBasedParser(object):
    """
    Lark-based Earley parser synthesized from the generator grammar.
    "Hard"; only parses things that are exactly in the grammar.
    """

    def __init__(self, grammar_rules):
        assert isinstance(grammar_rules, dict)
        # We need to destructively modify the rules a bit
        rules = deepcopy(grammar_rules)
        rch_to_ebnf = ToEBNF()
        as_ebnf = ""
        void_remover = DiscardVoid()
        meta_remover = DiscardMeta()

        all_wildcard_lhs = [non_term for non_term, _ in rules.items() if isinstance(non_term, WildCard)]
        if len(all_wildcard_lhs) == 0:
            all_rule_trees = [tree for _, productions in rules.items() for tree in productions]
            # Meta info doesn't affect the text of the command
            for tree in all_rule_trees:
                meta_remover.visit(tree)
                void_remover.visit(tree)
            wildcards = get_wildcards_forest(all_rule_trees)
            # We're gonna hallucinate some rules for the wildcards
            # * They can appear just as their string representation (should be what comes out of the generator)
            # * They can appear anonymized, like location0 or name0, but we can't know how they'd be numbered
            #   - If placement and beacon both appeared in a sentence, they'd be mapped to location0 and 1
            #   - We'll overaccept to counter this
            anon_kb = AnonymizedKnowledgebase()
            gen = Generator(anon_kb)
            for wildcard in wildcards:
                anon_replacements = list(gen.generate_groundings(expr_builder(wildcard), ignore_types=True))
                rules[wildcard] = [expr_builder(wildcard.to_human_readable())] + anon_replacements

        for non_term, productions in rules.items():
            # TODO: bake this into WildCard and NonTerminal types
            non_term_name = non_term.name.lower()
            if isinstance(non_term, WildCard):
                if non_term.name == "void":
                    # Void rules are for producing metadata during generation, they don't help during parsing
                    # because we'll never see this metadata as input
                    continue
                non_term_name = "wild_" + non_term.to_snake_case()
                # Question marks aren't allowed in non-term names
                non_term_name = non_term_name.replace("?", "obf")
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
        self._parser = Lark(as_ebnf, start='main')

    def __call__(self, utterance):
        try:
            return self._parser.parse(utterance)
        except lark.exceptions.LarkError as e:  # noqa: F841
            # If you want to see what part didn't fall in the grammar
            # print(e)
            return None


class KNearestNeighborParser(object):
    """
    A wrapper class that maps out-of-grammar sentences to their nearest neighbor by edit distance.
    """

    def __init__(self, neighbors, k=3, distance_threshold=float("inf"), confidence_threshold=None,
                 metric=editdistance.eval):
        assert (k > 0)
        self.neighbors = neighbors
        self.distance_threshold = distance_threshold
        self.k = k
        self.metric = metric

    def __call__(self, utterance):
        q = PriorityQueue()
        index = count(0)
        for neighbor, parse in self.neighbors:
            d = self.metric(neighbor, utterance)
            # index is just to break ties in the case that multiple neighbors have the same distance
            # Note that this makes us prefer neighbors that are compared earlier
            q.put_nowait((d, next(index), (neighbor, parse)))
            if d == 0:
                # Exact match returns the known parse
                return parse

        # Get the top k (lowest distance/priority) and see how they vote
        answer_votes = {}
        for i in range(self.k):
            d, _, (neighbor, parse) = q.get()
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
