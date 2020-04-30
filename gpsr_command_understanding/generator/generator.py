import copy
import re
from collections import defaultdict
from string import printable

import importlib_resources
from lark import Lark, Tree, exceptions

from gpsr_command_understanding.generator.grammar import TypeConverter, expand_shorthand, NonTerminal, \
    CombineExpressions, DiscardVoid, ComplexWildCard
from gpsr_command_understanding.util import replace_child_in_tree, \
    get_wildcards, has_nonterminals, ParseForward


GENERATOR_GRAMMARS = {2018: importlib_resources.read_text("gpsr_command_understanding.resources", "generator.lark"),
                      2019: importlib_resources.read_text("gpsr_command_understanding.resources", "generator.lark")}


# TODO(nickswalker): Document these methods
class Generator:
    def __init__(self, knowledge_base, grammar_format_version=2018):
        self._grammar_format_version = grammar_format_version
        grammar_spec = GENERATOR_GRAMMARS[grammar_format_version]
        self.__grammar_parser = Lark(grammar_spec,
                                     start=['rule_start', 'expression_start'], parser="lalr",
                                     transformer=TypeConverter())
        self.rule_parser = ParseForward(self.__grammar_parser, "rule_start")
        self.sequence_parser = ParseForward(self.__grammar_parser, "expression_start")
        self.rules = {}
        self.knowledge_base = knowledge_base

    def parse_production_rule(self, line, expand=True):
        try:
            parsed = self.rule_parser.parse(line)
        except exceptions.LarkError as e:
            raise e

        if len(parsed.children) == 0:
            return None, []

        rhs_list_expanded = [parsed.children[1]]
        if expand:
            rhs_list_expanded = expand_shorthand(parsed.children[1])
        # print(parsed.pretty())
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

    def ground(self, tree, **kwargs):
        return next(self.generate_groundings(tree, **kwargs))

    def generate_groundings(self, tree, random_generator=None, ignore_types=False):
        assignments = self.generate_grounding_assignments(tree, random_generator=random_generator,
                                                          ignore_types=ignore_types)
        for assignment in assignments:
            grounded = copy.deepcopy(tree)
            for token, replacement in assignment.items():
                replace_child_in_tree(grounded, token, replacement)
            yield grounded

    def generate_grounding_assignments(self, tree, random_generator=None, ignore_types=False):  # noqa: C901

        wildcards = get_wildcards(tree)
        assignment = {}

        constraints = defaultdict(set)
        for wildcard in wildcards:
            if "pron" in wildcard.name:
                # FIXME(nickswalker): Something here about pointing to the nearest name
                continue
            # IDs impose uniqueness constraints.
            else:
                if wildcard.id:
                    constraints[wildcard] = set()
                    # Could be another instance of the same wildcard. It's constrained already so skip it
                    if wildcard in assignment:
                        continue
                    for other_wildcard, item_constraints in constraints.items():
                        # Any wildcard of the same name with a different ID needs to be different
                        if other_wildcard.name == wildcard.name and other_wildcard.id != wildcard.id:
                            constraints[wildcard].add(other_wildcard)
                else:
                    constraints[wildcard] = set()
                    # No id, so implicitly unique wrt to all wildcards with the same name
                    for other_wildcard, item_constraints in constraints.items():
                        # Any wildcard of the same name with a different ID needs to be different
                        if other_wildcard != wildcard and other_wildcard.name == wildcard.name:
                            constraints[wildcard].add(other_wildcard)
                if ignore_types and wildcard.type != "room":
                    continue
                if wildcard.name == "object" and wildcard.type:
                    constraints[wildcard].add(("type", wildcard.type))
                elif wildcard.name == "location" and wildcard.type:
                    # Location types are a shorthand for an attribute: ex isplacment
                    constraints[wildcard].add(("is" + wildcard.type, True))
                # TODO(nickswalker): Respect obfuscation
                # TODO(nickswalker): Object category constraints (EGPSR)
                if wildcard.conditions:
                    for key, value in wildcard.conditions.items():
                        constraints[wildcard].add((key, value))

        yield from self.__populate_with_constraints(tree, constraints, random_generator=random_generator)

    def __populate_with_constraints(self, tree, constraints, random_generator=None):  # noqa: C901
        wildcards = get_wildcards(tree)
        if not wildcards:
            assert len(constraints.values()) == len(constraints)
            yield constraints
            return
        wildcard = next(wildcards)
        item_constraints = constraints[wildcard]
        # What things are possibilities to fill this slot?
        if wildcard.name == "pron":
            candidates = ["them"]
        elif wildcard.name == "pron paj":
            candidates = ["their"]
        else:
            candidates = self.knowledge_base.by_name[wildcard.name]
        if random_generator:
            if random_generator:
                random_generator.shuffle(candidates)
        for candidate in candidates:
            if not isinstance(item_constraints, set):
                # We should have already replaced this wildcard if it has a fixed constraint
                assert False
            valid = True
            for constraint in item_constraints:
                if isinstance(constraint, ComplexWildCard):
                    # Constraints only point backwards, so this constraint is saying that current wildcard
                    # must be different from a previously fixed value
                    if candidate == constraints[constraint]:
                        valid = False
                elif isinstance(constraint, tuple):
                    # This is some attribute that must have a certain value
                    attribute_name, value = constraint
                    attributes_for_type = self.knowledge_base.attributes[wildcard.name]
                    if attribute_name not in attributes_for_type.keys():
                        raise RuntimeError(
                            attribute_name + " is not a valid attribute for wildcard type " + wildcard.name)
                    if attributes_for_type[attribute_name].get(candidate) != value:
                        valid = False
            if not valid:
                continue

            fixed = copy.deepcopy(constraints)
            fresh_tree = copy.deepcopy(tree)
            fixed[wildcard].clear()
            fixed[wildcard] = candidate
            replace_child_in_tree(fresh_tree, wildcard, candidate)
            yield from self.__populate_with_constraints(fresh_tree, fixed)

    def generate_random(self, start_symbols, random_generator=None, **kwargs):
        return next(
            self.generate(start_symbols,
                          branch_cap=1, random_generator=random_generator, **kwargs))

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
                if random_generator:
                    replace_token = random_generator.choice(replace_tokens)
                    productions = self.rules[replace_token]
                    if branch_cap:
                        productions = random_generator.sample(productions, k=min(branch_cap, len(productions)))
                    else:
                        # Use all of the branches
                        productions = self.rules[replace_token]
                        random_generator.shuffle(productions)
                else:
                    replace_token = replace_tokens[0]
                    productions = self.rules[replace_token]
                    if branch_cap:
                        productions = productions[:min(branch_cap, len(productions))]

                # Replace it every way we know how
                for production in productions:
                    modified_sentence = copy.deepcopy(sentence)
                    replace_child_in_tree(modified_sentence, replace_token, production, only_once=True)
                    # Generate the rest of the sentence recursively assuming this replacement
                    stack.append(modified_sentence)
            else:
                # If we couldn't replace anything else, this sentence is done!
                sentence = CombineExpressions().visit(sentence)
                # If we have unexpanded non-terminals, something is wrong with the rules
                assert not has_nonterminals(sentence)
                yield sentence

    def extract_metadata(self, tree):
        """
        Remove wildcard metadata from the tree and list it in another object
        :param tree: The tree to pull metadata from
        :return: a tuple of the modified tree and a dictionary mapping wildcards or indices in the tree to the metadata
        """
        # Process metadata on wildcards
        sentence_metadata = {}
        wildcards = list(tree.scan_values(lambda x: isinstance(x, ComplexWildCard)))
        for wildcard in wildcards:
            card_meta = wildcard.metadata
            if wildcard.name == "void":
                # These are going to get removed, so key by index
                index = tree.children.index(wildcard)

            else:
                index = wildcard
            sentence_metadata[index] = card_meta
            wildcard.metadata = None

        tree = DiscardVoid().visit(tree)
        return tree, sentence_metadata
