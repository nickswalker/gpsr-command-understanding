import os
from copy import deepcopy

from gpsr_semantic_parser.util import merge_dicts, get_wildcards, replace_child
from gpsr_semantic_parser.xml_parsers import ObjectParser, LocationParser, NameParser, GesturesParser

from gpsr_semantic_parser.types import  *

from lark import Lark, Tree, Transformer, Visitor, Discard


class TypeConverter(Transformer):
    def non_terminal(self, children):
        return NonTerminal(children[0])

    def wildcard(self, children):
        typed = children[0]
        type = typed.children[0] if len(typed.children) > 0 else None
        extra = typed.children[1] if len(typed.children) > 1 else None
        if "obj" in typed.data:
            if "alike" in typed.data:
                type = "alike"
                extra = typed.children[0] if len(typed.children) > 1 else None
            elif "known" in typed.data:
                type = "known"
                extra = typed.children[0] if len(typed.children) > 1 else None
            return WildCard("object", type, extra)
        elif "loc" in typed.data:
            if "beacon" in typed.data:
                type = "beacon"
                extra = typed.children[0] if len(typed.children) > 1 else None
            elif "placement" in typed.data:
                type ="placement"
                extra = typed.children[0] if len(typed.children) > 1 else None
            elif "room" in typed.data:
                type = "room"
                extra = typed.children[0] if len(typed.children) > 1 else None
            return WildCard("location", type, extra)
        elif "category" in typed.data:
            return WildCard("category", type)
        elif "gesture" in typed.data:
            return WildCard("gesture", type)
        elif "name" in typed.data:
            return WildCard("name", type)
        elif "pron" in typed.data:
            return WildCard("pron", type)
        elif "question" in typed.data:
            return WildCard("question", type)
        elif "void" in typed.data:
            return WildCard("void", type)


class DiscardVoid(Visitor):
    def expression(self, tree):
        tree.children = list(filter(lambda x: not ((isinstance(x, WildCard) or isinstance(x, Anonimized)) and x.name == "void"), tree.children))


generator_grammar_parser = Lark(open(os.path.abspath(os.path.dirname(__file__) + "/../resources/generator2018/generator_grammar_ebnf.txt")), start='start', parser="lalr", transformer=TypeConverter())


class ToString(Transformer):
    def __default__(self, data, children, meta):
        return " ".join(map(str, children))

    def non_terminal(self, children):
        return "${}".format(" ".join(children))

    def choice(self, children):
        output = "("
        for child in children:
            output += child + " | "
        return output[:-3] + ")"

    def rule(self, children):
        return "{} = {}".format(children[0], children[1])

    def predicate(self, children):
        return "({})".format(" ".join(map(str,children)))

    def lambda_abs(self, children):
        return "(λ{})".format(" ".join(map(str,children)))

    def __call__(self, *args, **kwargs):
        return self.transform(*args)


tree_printer = ToString()


class CombineExpressions(Visitor):
    """
    Grammars may generate multiple text fragments in a sequence. This will combine them
    :param tokens:
    :return: a list of tokens with no adjacent text fragments
    """
    def top_expression(self, tree):
        tree.data = "expression"
        self.expression(tree)

    def expression(self, tree):
        cleaned = []
        i = 0
        while i < len(tree.children):
            child = tree.children[i]
            # Not a fragment? Forward to output
            if not (isinstance(child, Tree) and child.data == "expression"):
                cleaned.append(child)
                i += 1
                continue
            # Otherwise, gather up the the next subsequence of fragments
            j = i + 1
            while j < len(tree.children):
                next_child = tree.children[j]
                if isinstance(next_child, Tree) and next_child.data == "expression":
                    j += 1
                    continue
                break
            cleaned.extend([c for t in tree.children[i:j] for c in t.children])
            i = j
        if i == len(tree.children) - 1:
            cleaned.append(tree.children[i])

        all_expanded = False
        while not all_expanded:
            i = 0
            while i < len(cleaned):
                child = cleaned[i]
                if isinstance(child, Tree) and child.data == "expression":
                    cleaned = cleaned[:i] + child.children + cleaned[i+1:]
                    break
                i += 1
            all_expanded = True
        tree.children = cleaned


def expand_shorthand(tree):
    in_progress = [tree]
    output = []
    while len(in_progress) != 0:
        current = in_progress.pop()
        choices = list(current.find_data("choice"))
        if len(choices) == 0:
            output.append(current)
            continue
        for choice in choices:
            for option in choice.children:
                choice_made_tree = deepcopy(tree)
                if choice_made_tree == choice:
                    in_progress.append(option)
                else:
                    choice_parent = list(choice_made_tree.find_pred(lambda subtree: any([child == choice for child in subtree.children])))[0]
                    replace_child(choice_parent, choice, option, only_once=True)
                    in_progress.append(choice_made_tree)

    return output


def parse_production_rule(line):
    parsed = generator_grammar_parser.parse(line)
    rhs_list_expanded = expand_shorthand(parsed.children[1])
    #print(line)
    #print(parsed.pretty())
    return parsed.children[0], rhs_list_expanded


def load_grammar(grammar_file_paths):
    """
    :param grammar_file_paths: list of file paths
    :return: dictionary with NonTerminal key and values for all productions
    """
    if isinstance(grammar_file_paths, str):
        grammar_file_paths = [grammar_file_paths]
    production_rules = {}
    for grammar_file_path in grammar_file_paths:
        with open(grammar_file_path) as f:
            for line in f:
                line = line.strip()
                if len(line) == 0 or line[0] != '$':
                    # We only care about lines that start with a nonterminal (denoted by $)
                    continue
                # print(line)
                # parse into possible productions
                lhs, rhs_productions = parse_production_rule(line)
                # print(lhs)
                # print(rhs_productions)
                # add to dictionary, if already there then append to list of rules
                # using set to avoid duplicates
                if lhs not in production_rules:
                    production_rules[lhs] = rhs_productions
                else:
                    production_rules[lhs].extend(rhs_productions)
    return production_rules


def make_anonymized_grounding_rules(wildcards, show_details=False):
    """
    Generates a single special-token substitution for each wildcard.
    :param wildcards:
    :return:
    """
    grounding_rules = {}
    for term in wildcards:
        if show_details:
            prod = Anonimized(term.to_human_readable())
        else:
            prod = Anonimized(term.name)
        grounding_rules[term] = [Tree("expression", [prod])]
    return grounding_rules


def load_wildcard_rules(objects_xml_file, locations_xml_file, names_xml_file, gestures_xml_file):
    """
    Loads in the grounding rules for all the wildcard classes.
    :param objects_xml_file:
    :param locations_xml_file:
    :param names_xml_file:
    :param gestures_xml_file:
    :return:
    """
    object_parser = ObjectParser(objects_xml_file)
    locations_parser = LocationParser(locations_xml_file)
    names_parser = NameParser(names_xml_file)
    gestures_parser = GesturesParser(gestures_xml_file)

    objects = object_parser.all_objects()
    objects = [[x] for x in objects]
    categories = object_parser.all_categories()
    categories = [[x] for x in categories]
    names = names_parser.all_names()
    names = [[x] for x in names]
    locations = locations_parser.get_all_locations()
    locations = [[x] for x in locations]
    rooms = locations_parser.get_all_rooms()
    rooms = [[x] for x in rooms]
    gestures = gestures_parser.get_gestures()
    gestures = [[x] for x in gestures]


    production_rules = {}
    # add objects
    production_rules[WildCard('object', "known")] = objects
    production_rules[WildCard('object', "alike")] = objects
    production_rules[WildCard('object')] = objects
    production_rules[WildCard('object1')] = objects
    production_rules[WildCard('object2')] = objects
    production_rules[WildCard('object', '1')] = objects
    production_rules[WildCard('object', '2')] = objects
    production_rules[WildCard('category')] = [["objects"]]
    production_rules[WildCard('category', '1')] = [["objects"]]
    production_rules[WildCard('object', 'known', obfuscated=True)] = categories
    production_rules[WildCard('object', 'alike', obfuscated=True)] = categories
    production_rules[WildCard('object', obfuscated=True)] = categories
    # add names
    production_rules[WildCard('name')] = names
    production_rules[WildCard('name', '1')] = names
    production_rules[WildCard('name', '2')] = names
    # add locations
    production_rules[WildCard('location', 'placement')] = locations
    production_rules[WildCard('location', 'placement', '1')] = locations
    production_rules[WildCard('location', 'placement', '2')] = locations
    production_rules[WildCard('location','beacon')] = locations
    production_rules[WildCard('location','beacon', '1')] = locations
    production_rules[WildCard('location','beacon','2')] = locations
    production_rules[WildCard('location','room')] = rooms
    production_rules[WildCard('location','room', '1')] = rooms
    production_rules[WildCard('location','room', '2')] = rooms
    production_rules[WildCard('location','placement', obfuscated=True)] = rooms
    production_rules[WildCard('location','beacon', obfuscated=True)] = rooms
    production_rules[WildCard('location','room', obfuscated=True)] = [["room"]]
    production_rules[WildCard('gesture')] = gestures

    for token, productions in production_rules.items():
        productions = list(map(lambda p: Tree("expression", p),productions))
        production_rules[token] = productions

    return production_rules


def prepare_rules(common_rules_path, category_paths, objects_xml_file, locations_xml_file, names_xml_file, gestures_xml_file):
    """
        Prepare the production rules for a given GPSR category.
        :param common_rules_path:
        :param category_path:
        :return:
        """
    if not isinstance(category_paths, list):
        category_paths = [category_paths]
    rules = load_grammar([common_rules_path] + category_paths)
    grounding_rules = load_wildcard_rules(objects_xml_file, locations_xml_file, names_xml_file, gestures_xml_file)
    # This part of the grammar won't lend itself to any useful generalization from rephrasings
    rules[WildCard("question")] = [Tree("expression",["question"])]
    rules[WildCard("pron")] = [Tree("expression",["them"])]
    return merge_dicts(rules, grounding_rules)


def prepare_anonymized_rules(common_rules_path, category_paths, show_debug_details=False):
    """
    Prepare the production rules for a given GPSR category, making some
    typical adjustments to make the grammar usable
    :param common_rules_path:
    :param category_path:
    :return:
    """
    if not isinstance(category_paths, list):
        category_paths = [category_paths]
    rules = load_grammar([common_rules_path] + category_paths)
    # $whattosay curiously doesn't pull from an XML file, but is instead baked into the grammar.
    # We'll manually anonymize it here
    rules[NonTerminal("whattosay")] = [Tree("expression",[Anonimized("whattosay")])]

    # We'll use the indeterminate pronoun for convenience
    rules[WildCard("pron")] = [Tree("expression",["them"])]
    all_rule_trees = [tree for _, trees  in rules.items() for tree in trees ]
    groundable_terms = get_wildcards(all_rule_trees)
    groundable_terms.add(WildCard("object", "1"))
    groundable_terms.add(WildCard("category", "1"))
    grounding_rules = make_anonymized_grounding_rules(groundable_terms, show_debug_details)
    return merge_dicts(rules, grounding_rules)