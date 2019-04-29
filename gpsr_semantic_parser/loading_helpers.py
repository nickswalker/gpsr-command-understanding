from os.path import join

from lark import Tree

from gpsr_semantic_parser.tokens import Anonymized, WildCard
from gpsr_semantic_parser.util import merge_dicts, get_wildcards
from gpsr_semantic_parser.xml_parsers import ObjectParser, LocationParser, NameParser, GesturesParser


def make_anonymized_grounding_rules(wildcards, show_details=False):
    """
    Generates a single special-token substitution for each wildcard.
    :param wildcards:
    :return:
    """
    grounding_rules = {}
    for term in wildcards:
        if show_details:
            prod = Anonymized(term.to_human_readable())
        else:
            prod = Anonymized(term.name)
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
    objects = [[x] for x in sorted(objects)]
    categories = object_parser.all_categories()
    categories = [[x] for x in sorted(categories)]
    names = names_parser.all_names()
    names = [[x] for x in sorted(names)]
    locations = locations_parser.get_all_locations()
    locations = [[x] for x in sorted(locations)]
    rooms = locations_parser.get_all_rooms()
    rooms = [[x] for x in sorted(rooms)]
    gestures = gestures_parser.get_gestures()
    gestures = [[x] for x in sorted(gestures)]


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


    things_to_say = ["something about yourself","the time","what day it is","the day of the week","a joke"]
    production_rules[WildCard("whattosay")] = [ [x] for x in things_to_say]

    for token, productions in production_rules.items():
        productions = list(map(lambda p: Tree("expression", p),productions))
        production_rules[token] = productions

    return production_rules


def load_all_2018(generator, grammar_dir):

    common_path = join(grammar_dir, "common_rules.txt")

    paths = tuple(map(lambda x: join(grammar_dir, x), ["objects.xml", "locations.xml", "names.xml", "gestures.xml"]))

    cat1_rules = generator.load_rules([common_path, join(grammar_dir, "gpsr_category_1_grammar.txt")])
    cat2_rules = generator.load_rules([common_path, join(grammar_dir, "gpsr_category_2_grammar.txt")])
    cat3_rules = generator.load_rules([common_path, join(grammar_dir, "gpsr_category_3_grammar.txt")])

    cat1_rules_ground = prepare_grounded_rules(generator, common_path, join(grammar_dir, "gpsr_category_1_grammar.txt"), *paths)
    cat2_rules_ground = prepare_grounded_rules(generator, common_path, join(grammar_dir, "gpsr_category_2_grammar.txt"), *paths)
    cat3_rules_ground = prepare_grounded_rules(generator, common_path, join(grammar_dir, "gpsr_category_3_grammar.txt"), *paths)
    cat1_rules_anon = prepare_anonymized_rules(generator, common_path, join(grammar_dir, "gpsr_category_1_grammar.txt"))
    cat2_rules_anon = prepare_anonymized_rules(generator, common_path, join(grammar_dir, "gpsr_category_2_grammar.txt"))
    cat3_rules_anon = prepare_anonymized_rules(generator, common_path, join(grammar_dir, "gpsr_category_3_grammar.txt"))

    cat1_semantics = generator.load_semantics_rules(join(grammar_dir, "gpsr_category_1_semantics.txt"))
    cat2_semantics = generator.load_semantics_rules(
        [join(grammar_dir, "gpsr_category_1_semantics.txt"), join(grammar_dir, "gpsr_category_2_semantics.txt")])
    cat3_semantics = generator.load_semantics_rules(join(grammar_dir, "gpsr_category_3_semantics.txt"))

    return [(cat1_rules, cat1_rules_anon, cat1_rules_ground, cat1_semantics), (cat2_rules, cat2_rules_anon, cat2_rules_ground, cat2_semantics), (cat3_rules, cat3_rules_anon, cat3_rules_ground, cat3_semantics)]

def load_slot(generator, grammar_dir):
    common_path = join(grammar_dir, "common_rules.txt")

    paths = tuple(map(lambda x: join(grammar_dir, x), ["objects.xml", "locations.xml", "names.xml", "gestures.xml"]))

    cat1_rules = generator.load_rules([common_path, join(grammar_dir, "gpsr_category_1_grammar.txt")])
    cat1_rules_ground = prepare_grounded_rules(generator, common_path, join(grammar_dir, "gpsr_category_1_grammar.txt"), *paths)
    cat1_rules_anon = prepare_anonymized_rules(generator, common_path, join(grammar_dir, "gpsr_category_1_grammar.txt"))
    cat1_semantics = generator.load_semantics_rules([join(grammar_dir, "gpsr_category_1_slot.txt"), join(grammar_dir, "common_rules_slot.txt")])
    #cat1_semantics = generator.load_semantics_rules([join(grammar_dir, "gpsr_category_1_semantics.txt")])

    return [(cat1_rules, cat1_rules_anon, cat1_rules_ground, cat1_semantics)]

