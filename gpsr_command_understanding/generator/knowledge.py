from collections import defaultdict

import importlib_resources

from gpsr_command_understanding.generator.xml_parsers import ObjectParser, LocationParser, NameParser, GesturesParser, \
    QuestionParser


class KnowledgeBase:
    def __init__(self, items, attributes):
        self.by_name = items
        self.attributes = attributes

    @staticmethod
    def from_xml_dir(xml_path):
        raw_ontology_xml = list(map(lambda x: importlib_resources.open_text(xml_path, x),
                                     ["objects.xml", "locations.xml", "names.xml", "gestures.xml", "questions.xml", "whattosay.txt"]))
        kb = KnowledgeBase.from_xml(*raw_ontology_xml)
        # Clean up IO to avoid warnings
        for stream in raw_ontology_xml:
            stream.close()
        return kb

    @staticmethod
    def from_xml(objects_xml_file, locations_xml_file, names_xml_file, gestures_xml_file,
                 questions_xml_file, sayings_file = None):
        object_parser = ObjectParser(objects_xml_file)
        locations_parser = LocationParser(locations_xml_file)
        names_parser = NameParser(names_xml_file)
        gestures_parser = GesturesParser(gestures_xml_file)
        question_parser = QuestionParser(questions_xml_file)
        sayings = ["a joke"]
        if sayings_file:
                sayings = sayings_file.readlines()
                sayings = list(map(str.strip, sayings))

        objects = object_parser.all_objects()
        categories = object_parser.all_categories()
        names = names_parser.all_names()
        locations = locations_parser.get_all_locations()
        gestures = list(gestures_parser.get_gestures())
        questions = list(question_parser.get_question_answer_dict().keys())
        attributes = {"object": object_parser.get_attributes(), "location": locations_parser.get_attributes()}

        attributes["object"]["category"] = object_parser.get_objects_to_categories()
        attributes["location"]["in"] = locations_parser.get_room_locations_are_in()

        by_name = {
            "object": objects,
            "category": categories,
            "name": names,
            "location": locations,
            "gesture": gestures,
            "question": questions,
            "whattosay": sayings
        }
        return KnowledgeBase(by_name, attributes)


class AnonymizedKnowledgebase:
    def __init__(self):
        names = [
            "object",
            "category",
            "name",
            "location",
            "gesture",
            "question",
            "whattosay"
        ]
        rooms = ["room" + str(i) for i in range(3)]
        self.by_name = {name: [name + str(i) for i in range(3)] for name in names}
        self.by_name["location"] += rooms
        self.attributes = {"object": {"type": defaultdict(lambda: True),
                                      "category": defaultdict(lambda: "c1")},
                           "location": {"isplacement": defaultdict(lambda: True),
                                        "isbeacon": defaultdict(lambda: True),
                                        "isroom": defaultdict(lambda: False),
                                        "in": defaultdict(lambda: "room1")}}
        for room in rooms:
            self.attributes["location"]["isroom"][room] = True
