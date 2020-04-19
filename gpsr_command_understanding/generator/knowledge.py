import importlib_resources

from gpsr_command_understanding.generator.xml_parsers import ObjectParser, LocationParser, NameParser, GesturesParser, \
    QuestionParser


class KnowledgeBase:
    def __init__(self, items, attributes):
        self.by_name = items
        self.attributes = attributes

    @staticmethod
    def from_xml_dir(xml_path):
        raw_ontology_xml = tuple(map(lambda x: importlib_resources.open_text(xml_path, x),
                                     ["objects.xml", "locations.xml", "names.xml", "gestures.xml", "questions.xml"]))
        kb = KnowledgeBase.from_xml(*raw_ontology_xml)
        # Clean up IO to avoid warnings
        for stream in raw_ontology_xml:
            stream.close()
        return kb

    @staticmethod
    def from_xml(objects_xml_file, locations_xml_file, names_xml_file, gestures_xml_file,
                      questions_xml_file):
        object_parser = ObjectParser(objects_xml_file)
        locations_parser = LocationParser(locations_xml_file)
        names_parser = NameParser(names_xml_file)
        gestures_parser = GesturesParser(gestures_xml_file)
        question_parser = QuestionParser(questions_xml_file)

        objects = object_parser.all_objects()
        categories = object_parser.all_categories()
        names = names_parser.all_names()
        locations = locations_parser. \
            get_all_locations()
        beacons = locations_parser.get_all_beacons()
        placements = locations_parser.get_all_placements()
        rooms = locations_parser.get_all_rooms()
        gestures = list(gestures_parser.get_gestures())
        questions = list(question_parser.get_question_answer_dict().keys())
        attributes = {"object": object_parser.get_attributes()}

        attributes["object"]["category"] = object_parser.get_objects_to_categories()

        by_name = {
            "object": objects,
            "category": categories,
            "name": names,
            "location": locations,
            "beacon": beacons,
            "placement": placements,
            "room": rooms,
            "gesture": gestures,
            "question": questions,
            # FIXME: Load these from somewhere
            "whattosay": ["a joke"]
        }
        return KnowledgeBase(by_name, attributes)

