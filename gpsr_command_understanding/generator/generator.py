import copy
import re
from collections import defaultdict
from string import printable

import importlib_resources
from lark import Lark, Tree, exceptions


from gpsr_command_understanding.generator.grammar import TypeConverter, expand_shorthand, NonTerminal, \
    CombineExpressions, DiscardVoid
from gpsr_command_understanding.util import has_placeholders, replace_child_in_tree, \
    get_wildcards, has_nonterminals
from gpsr_command_understanding.generator.grammar import tree_printer

try:
    from itertools import izip_longest as zip_longest
except ImportError:
    from itertools import zip_longest

GENERATOR_GRAMMARS = {2018: importlib_resources.read_text("gpsr_command_understanding.resources", "generator.lark"),
                      2019: importlib_resources.read_text("gpsr_command_understanding.resources", "generator.lark")}


# TODO(nickswalker): Document these methods
class Generator:
    def __init__(self, knowledge_base, grammar_format_version=2018):
        self._grammar_format_version = grammar_format_version
        grammar_spec = GENERATOR_GRAMMARS[grammar_format_version]
        self.grammar_parser = Lark(grammar_spec,
                                   start='rule_start', parser="lalr", transformer=TypeConverter())
        self.sequence_parser = Lark(grammar_spec,
                                    start='expression_start', parser="lalr", transformer=TypeConverter())
        self.rules = {}
        self.knowledge_base = knowledge_base

    def parse_production_rule(self, line, expand=True):
        try:
            parsed = self.grammar_parser.parse(line)
        except exceptions.LarkError as e:
            raise e

        if len(parsed.children) == 0:
            return None, []

        rhs_list_expanded = [parsed.children[1]]
        if expand:
            rhs_list_expanded = expand_shorthand(parsed.children[1])
        #print(parsed.pretty())
        return parsed.children[0], rhs_list_expanded

    def load_rules(self, grammar_files, expand_shorthand=True):
        """
        :param grammar_files: list of files
        :return: dictionary with NonTerminal key and values for all productions
        """
        if not isinstance(grammar_files, list):
            grammar_files = [grammar_files]

        i = 0
        for grammar_file in grammar_files:
            for line in grammar_file:
                # Scrub out any non-printable characters; some grammar files have annoying byte order
                # markers attached
                line = line.strip()
                line = re.sub("[^{}]+".format(printable), "", line)
                # parse into possible productions
                lhs, rhs_productions = self.parse_production_rule(line, expand_shorthand)
                # Skip emtpy LHS (comments)
                # add to dictionary, if already there then append to list of rules
                # using set to avoid duplicates
                if not lhs:
                    continue
                elif lhs not in self.rules:
                    self.rules[lhs] = rhs_productions
                    i += 1
                else:
                    self.rules[lhs].extend(rhs_productions)
                    i += 1
        return i

    def ground(self, tree, random_source=None):
        return next(self.generate_groundings(tree, random_source=random_source))

    def generate_groundings(self, tree, random_source=None):
        assignments = self.generate_grounding_assignment(tree, random_source)
        for assignment in assignments:
            grounded = copy.deepcopy(tree)
            for token, replacement in assignment.items():
                replace_child_in_tree(grounded, token, replacement)
            yield grounded

    def generate_grounding_assignment(self, tree, random_source=None):
        wildcards = get_wildcards(tree)
        assignment = {}

        constraints = defaultdict(set)
        for wildcard in wildcards:
            # Could be another instance of the same wildcard
            if wildcard.name == "pron":
                # FIXME(nickswalker): Something here about pointing to the nearest name
                pass
            elif wildcard.id:
                constraints[wildcard] = set()
                if wildcard in assignment:
                    continue
                for other_wildcard, item_constraints in constraints.items():
                    # Any wildcard of the same name with a different ID needs to be different
                    if other_wildcard.name == wildcard.name and other_wildcard.id != wildcard.id:
                        constraints[wildcard].add(other_wildcard)

        yield from self.__populate_with_constraints(tree, constraints)

    def __populate_with_constraints(self, tree, constraints, random_source=None):
        wildcards = get_wildcards(tree)
        if not wildcards:
            yield constraints
            return
        wildcard = next(wildcards)
        item_constraints = constraints[wildcard]
        if wildcard.name == "pron":
            candidates = ["them"]
        else:
            candidates = self.knowledge_base.by_name[wildcard.name]
        if random_source:
            pass
        for candidate in candidates:
            if isinstance(item_constraints, set):
                valid = True
                for constraint in item_constraints:
                    # Constraints only point backwards, so this constraint is saying that current wildcard
                    # must be different from a previously fixed value
                    if candidate == constraints[constraint]:
                        valid = False
                if not valid:
                    continue
            else:
                # We should have already replaced this wildcard if it has a fixed constraint
                assert False
            fixed = copy.deepcopy(constraints)
            fresh_tree = copy.deepcopy(tree)
            fixed[wildcard].clear()
            fixed[wildcard] = candidate
            replace_child_in_tree(fresh_tree, wildcard, candidate)
            yield from self.__populate_with_constraints(fresh_tree, fixed)

    def generate(self, start_tree, branch_cap=None, random_generator=None):
        """
        A generator that produces completely expanded sentences in depth-first order
        :param start_tree: the list of tokens to begin expanding
        :param production_rules: the rules to use for expanding the tokens
        """
        # Make sure the start point is a Tree
        if isinstance(start_tree, NonTerminal):
            stack = [Tree("expression", [start_tree])]
        elif isinstance(start_tree, list):
            stack = [Tree("expression", start_tree)]
        else:
            stack = [start_tree]

        while len(stack) != 0:
            sentence = stack.pop()
            replace_tokens = list(sentence.scan_values(lambda x: x in self.rules.keys()))
            if replace_tokens:
                replace_token = replace_tokens[0]
                # Replace it every way we know how
                for production in self.rules[replace_token]:
                    modified_sentence = copy.deepcopy(sentence)
                    replace_child_in_tree(modified_sentence, replace_token, production, only_once=True)
                    # Generate the rest of the sentence recursively assuming this replacement
                    stack.append(modified_sentence)
            else:
                # If we couldn't replace anything else, this sentence is done!
                sentence = CombineExpressions().visit(sentence)
                sentence = DiscardVoid().visit(sentence)
                # If we have unexpanded non-terminals, something is wrong with the rules
                assert not has_nonterminals(sentence)
                yield sentence
