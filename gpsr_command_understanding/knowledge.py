import importlib_resources

from gpsr_command_understanding.xml_parsers import ObjectParser, LocationParser, NameParser, GesturesParser, \
    QuestionParser


class KnowledgeBase:
    def __init__(self):
        pass

    def load_from_xml_dir(self, xml_path):
        raw_ontology_xml = tuple(map(lambda x: importlib_resources.open_text(xml_path, x),
                                     ["objects.xml", "locations.xml", "names.xml", "gestures.xml", "questions.xml"]))
        self.load_from_xml(*raw_ontology_xml)
        # Clean up IO to avoid warnings
        for stream in raw_ontology_xml:
            stream.close()

    def load_from_xml(self, objects_xml_file, locations_xml_file, names_xml_file, gestures_xml_file,
                      questions_xml_file):
        object_parser = ObjectParser(objects_xml_file)
        locations_parser = LocationParser(locations_xml_file)
        names_parser = NameParser(names_xml_file)
        gestures_parser = GesturesParser(gestures_xml_file)
        question_parser = QuestionParser(questions_xml_file)

        self.objects = object_parser.all_objects()
        self.categories = object_parser.all_categories()
        self.names = names_parser.all_names()
        self.locations = locations_parser. \
            get_all_locations()
        self.beacons = locations_parser.get_all_beacons()
        self.placements = locations_parser.get_all_placements()
        self.rooms = locations_parser.get_all_rooms()
        self.gestures = gestures_parser.get_gestures()
        self.questions = question_parser.get_question_answer_dict()

        self.by_name = {
            "object": self.objects,
            "category": self.categories,
            "name": self.names,
            "location": self.locations,
            "beacon": self.beacons,
            "placement": self.placements,
            "room": self.rooms,
            "gesture": self.gestures,
            "question": self.questions,
        }
