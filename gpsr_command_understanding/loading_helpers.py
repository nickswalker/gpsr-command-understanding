from os.path import join

from lark import Tree

from gpsr_command_understanding.tokens import WildCard
from gpsr_command_understanding.xml_parsers import ObjectParser, LocationParser, NameParser, GesturesParser


def load_entities_from_xml(objects_xml_file, locations_xml_file, names_xml_file, gestures_xml_file):
    object_parser = ObjectParser(objects_xml_file)
    locations_parser = LocationParser(locations_xml_file)
    names_parser = NameParser(names_xml_file)
    gestures_parser = GesturesParser(gestures_xml_file)

    objects = object_parser.all_objects()
    categories = object_parser.all_categories()
    names = names_parser.all_names()
    locations = locations_parser.\
        get_all_locations()
    beacons = locations_parser.get_all_beacons()
    placements = locations_parser.get_all_placements()
    rooms = locations_parser.get_all_rooms()
    gestures = gestures_parser.get_gestures()

    return objects, categories, names, locations, beacons, placements, rooms, gestures


def load_wildcard_rules(objects, categories, names, locations, beacons, placements, rooms, gestures):
    """
    Loads in the grounding rules for all the wildcard classes.
    :param objects_xml_file:
    :param locations_xml_file:
    :param names_xml_file:
    :param gestures_xml_file:
    :return:
    """
    objects = [[x] for x in sorted(objects)]
    categories = [[x] for x in sorted(categories)]
    names = [[x] for x in sorted(names)]
    locations = [[x] for x in sorted(locations)]
    beacons = [[x] for x in sorted(beacons)]
    placements = [[x] for x in sorted(placements)]
    rooms = [[x] for x in sorted(rooms)]
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
    production_rules[WildCard('category')] = categories
    production_rules[WildCard('category', '1')] = categories
    production_rules[WildCard('object', 'known', obfuscated=True)] = categories
    production_rules[WildCard('object', 'alike', obfuscated=True)] = categories
    production_rules[WildCard('object', obfuscated=True)] = categories
    # add names
    production_rules[WildCard('name')] = names
    production_rules[WildCard('name', '1')] = names
    production_rules[WildCard('name', '2')] = names
    # add locations
    production_rules[WildCard('location', 'placement')] = placements
    production_rules[WildCard('location', 'placement', '1')] = placements
    production_rules[WildCard('location', 'placement', '2')] = placements
    production_rules[WildCard('location','beacon')] = beacons
    production_rules[WildCard('location','beacon', '1')] = beacons
    production_rules[WildCard('location','beacon','2')] = beacons
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


def load_all_2018_by_cat(generator, grammar_dir, expand_shorthand=True):

    common_path = join(grammar_dir, "common_rules.txt")

    paths = tuple(map(lambda x: join(grammar_dir, x), ["objects.xml", "locations.xml", "names.xml", "gestures.xml"]))
    entities = load_entities_from_xml(*paths)

    cat1_rules = generator.load_rules([common_path, join(grammar_dir, "gpsr_category_1_grammar.txt")])
    cat2_rules = generator.load_rules([common_path, join(grammar_dir, "gpsr_category_2_grammar.txt")])
    cat3_rules = generator.load_rules([common_path, join(grammar_dir, "gpsr_category_3_grammar.txt")])

    cat1_rules_ground = generator.prepare_grounded_rules([common_path, join(grammar_dir, "gpsr_category_1_grammar.txt")], entities)
    cat2_rules_ground = generator.prepare_grounded_rules([common_path, join(grammar_dir, "gpsr_category_2_grammar.txt")], entities)
    cat3_rules_ground = generator.prepare_grounded_rules([common_path, join(grammar_dir, "gpsr_category_3_grammar.txt")], entities)
    cat1_rules_anon = generator.prepare_anonymized_rules([common_path, join(grammar_dir, "gpsr_category_1_grammar.txt")])
    cat2_rules_anon = generator.prepare_anonymized_rules([common_path, join(grammar_dir, "gpsr_category_2_grammar.txt")])
    cat3_rules_anon = generator.prepare_anonymized_rules([common_path, join(grammar_dir, "gpsr_category_3_grammar.txt")])

    cat1_semantics = generator.load_semantics_rules(join(grammar_dir, "gpsr_category_1_semantics.txt"))
    cat2_semantics = generator.load_semantics_rules(
        [join(grammar_dir, "gpsr_category_1_semantics.txt"), join(grammar_dir, "gpsr_category_2_semantics.txt")])
    cat3_semantics = generator.load_semantics_rules(join(grammar_dir, "gpsr_category_3_semantics.txt"))

    return [(cat1_rules, cat1_rules_anon, cat1_rules_ground, cat1_semantics), (cat2_rules, cat2_rules_anon, cat2_rules_ground, cat2_semantics), (cat3_rules, cat3_rules_anon, cat3_rules_ground, cat3_semantics)]


def load_all_2018(generator, grammar_dir, expand_shorthand=True):

    common_path = join(grammar_dir, "common_rules.txt")

    paths = tuple(map(lambda x: join(grammar_dir, x), ["objects.xml", "locations.xml", "names.xml", "gestures.xml"]))
    entities = load_entities_from_xml(*paths)
    grammar_files = [common_path, join(grammar_dir, "gpsr_category_1_grammar.txt"), join(grammar_dir, "gpsr_category_2_grammar.txt"), join(grammar_dir, "gpsr_category_3_grammar.txt")]
    rules = generator.load_rules(grammar_files)

    rules_ground = generator.prepare_grounded_rules(grammar_files, entities)
    rules_anon = generator.prepare_anonymized_rules(grammar_files)

    semantics = generator.load_semantics_rules(
        [join(grammar_dir, "gpsr_category_1_semantics.txt"), join(grammar_dir, "gpsr_category_2_semantics.txt"),  join(grammar_dir, "gpsr_category_3_semantics.txt")])

    return rules, rules_anon, rules_ground, semantics, entities


def load_all_2019(generator, grammar_dir, expand_shorthand=True):

    common_path = join(grammar_dir, "common_rules.txt")

    paths = tuple(map(lambda x: join(grammar_dir, x), ["objects.xml", "locations.xml", "names.xml", "gestures.xml"]))
    entities = load_entities_from_xml(*paths)

    rules = generator.load_rules([common_path, join(grammar_dir, "gpsr.txt")], expand_shorthand=expand_shorthand)
    rules_ground = generator.prepare_grounded_rules([common_path, join(grammar_dir, "gpsr.txt")], entities)
    rules_anon = generator.prepare_anonymized_rules([common_path, join(grammar_dir, "gpsr.txt")])

    semantics = generator.load_semantics_rules(join(grammar_dir, "gpsr_semantics.txt"))

    return rules, rules_anon, rules_ground, semantics, entities