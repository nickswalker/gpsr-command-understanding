from gpsr_semantic_parser.util import combine_adjacent_text_fragments, expand_shorthand, merge_dicts
from gpsr_semantic_parser.xml_parsers import ObjectParser, LocationParser, NameParser, GesturesParser

from gpsr_semantic_parser.types import  *

import re


def tokenize(raw_rule):
    """
    Tokenize a GSPR grammar production rule
    :param raw_rule:
    :return: a list of tokens
    """
    tokens = []
    cursor = 0
    while cursor != len(raw_rule):
        char = raw_rule[cursor]
        if char == DOLLAR:
            match = re.search(NON_TERM_RE, raw_rule[cursor:])
            name = match.groupdict()["name"]
            tokens.append(NonTerminal(name))
            cursor += match.end()
        elif char == L_PAREN:
            tokens.append(L_PAREN)
            cursor += 1
        elif char == R_PAREN:
            tokens.append(R_PAREN)
            cursor += 1
        elif char == BAR:
            tokens.append(BAR)
            cursor += 1
        elif char == L_C_BRACE:
            # We'll grab a string where the braces are balanced
            count = 1
            end_cursor = cursor + 1
            while count != 0:
                if raw_rule[end_cursor] == L_C_BRACE:
                    count += 1
                elif raw_rule[end_cursor] == R_C_BRACE:
                    count -= 1
                end_cursor += 1
            has_void = raw_rule.find("void", cursor, end_cursor)
            if has_void != -1:
                # Just grab the stuff past the "void" and before the closing brace
                tokens.append(Void(raw_rule[has_void + 4:end_cursor-1]))
                cursor = end_cursor
                continue

            has_meta = raw_rule.find("meta",cursor, end_cursor)
            meta_removed = raw_rule[cursor: end_cursor]
            if has_meta != -1:
                meta_removed = raw_rule[cursor:has_meta] + "}"

            match = re.search(WILDCARD_RE, meta_removed)
            name = match.groupdict()["name"]

            if name in WILDCARD_ALIASES.keys():
                inner_string = match.group().replace(name, " ".join(WILDCARD_ALIASES[name]))
                match = re.search(WILDCARD_RE, inner_string)
            name = match.groupdict()["name"]
            type = match.groupdict()["type"]
            extra = match.groupdict()["extra"]
            obfuscated = match.groupdict()["obfuscated"] != None
            tokens.append(WildCard(name, type, extra, obfuscated))
            cursor = end_cursor
        elif char.isspace():
            match = re.search(WHITESPACE_RE, raw_rule[cursor:])
            cursor += match.end()
        else:
            match = re.search(EMPTY_STR_RE, raw_rule[cursor:])
            if match:
                tokens.append(TextFragment(""))
            else:
                match = re.search(TEXT_FRAG_RE, raw_rule[cursor:])
                assert "meta" not in match.group()
                tokens.append(TextFragment(match.group()))
            assert match.end() > 0
            cursor += match.end()

    return tokens


def parse_production_rule(line):
    eq_split = line.split("=")
    # rule should be a single nonterminal producing some mix of term/non-term
    assert (len(eq_split) == 2)
    head, expansion = eq_split
    lhs = NonTerminal(head.strip()[1:])
    rhs_raw = expansion.strip()
    rhs_tokens = tokenize(rhs_raw)
    rhs_list_expanded = expand_shorthand([], rhs_tokens, "ALPH", [])
    rhs_list_expanded = [combine_adjacent_text_fragments(x) for x in rhs_list_expanded]
    return lhs, rhs_list_expanded


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


def get_wildcards(production_rules):
    """
    Get all wildcards that occur in a grammar
    :param production_rules:
    :return:
    """
    groundable_terms = set()
    for non_term, rule_list in production_rules.items():
        for rule in rule_list:
            for token in rule:
                if isinstance(token, WildCard):
                    groundable_terms.add(token)
    return groundable_terms


def make_mock_wildcard_rules(wildcards):
    """
    Generates a single substitution for each wildcard. Helpful for testing.
    :param wildcards:
    :return:
    """
    grounding_rules = {}
    for term in wildcards:
        grounding_rules[term] = [["<{}>".format(term.name)]]
    return grounding_rules


def load_wildcard_rules(objects_xml_file, locations_xml_file, names_xml_file, gestures_xml_file):
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
    production_rules[WildCard('kobject')] = objects
    production_rules[WildCard('aobject')] = objects
    production_rules[WildCard('object')] = objects
    production_rules[WildCard('object1')] = objects
    production_rules[WildCard('object2')] = objects
    production_rules[WildCard('object 1')] = objects
    production_rules[WildCard('object 2')] = objects
    production_rules[WildCard('category')] = "objects"
    production_rules[WildCard('kobject', True)] = categories
    production_rules[WildCard('aobject', True)] = categories
    production_rules[WildCard('object', True)] = categories
    # add names
    production_rules[WildCard('name')] = names
    production_rules[WildCard('name 1')] = names
    production_rules[WildCard('name 2')] = names
    # add locations
    production_rules[WildCard('placement')] = locations
    production_rules[WildCard('placement 1')] = locations
    production_rules[WildCard('placement 2')] = locations
    production_rules[WildCard('beacon')] = locations
    production_rules[WildCard('beacon 1')] = locations
    production_rules[WildCard('beacon 2')] = locations
    production_rules[WildCard('room')] = rooms
    production_rules[WildCard('room 1')] = rooms
    production_rules[WildCard('room 2')] = rooms
    production_rules[WildCard('placement', True)] = rooms
    production_rules[WildCard('beacon', True)] = rooms
    production_rules[WildCard('room', True)] = "room"
    production_rules[WildCard('gesture')] = gestures

    return production_rules


def prepare_rules(common_rules_path, category_paths):
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
    rules[NonTerminal("whattosay")] = [[TextFragment("<whattosay>")]]
    groundable_terms = get_wildcards(rules)
    grounding_rules = make_mock_wildcard_rules(groundable_terms)
    # There are too many wildcard options for this to workable during testing
    #grounding_rules = load_wildcard_rules(join(grammar_dir, "objects.xml"),join(grammar_dir, "locations.xml"),join(grammar_dir, "names.xml"))
    return merge_dicts(rules, grounding_rules)