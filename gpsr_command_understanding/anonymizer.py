import re
from collections import defaultdict


class Anonymizer(object):
    def __init__(self, objects, categories, names, locations, rooms, gestures):
        self.names = names
        self.categories = categories
        self.locations = locations
        self.rooms = rooms
        self.objects = objects
        self.gestures = gestures
        replacements = {}
        for name in self.names:
            replacements[name] = "name"

        for location in self.locations:
            replacements[location] = "location"

        for room in self.rooms:
            replacements[room] = "room"

        # Note they're we're explicitly clumping beacons and placements (which may overlap)
        # together to make anonymizing/parsing easier.
        """
        for beacon in self.beacons:
            replacements[beacon] = "location beacon"

        for placement in self.placements:
            replacements[placement] = "location placement"
        """
        for object in self.objects:
            replacements[object] = "object"

        for gesture in self.gestures:
            replacements[gesture] = "gesture"

        for category in self.categories:
            replacements[category] = "category"

        self.rep = replacements
        escaped = dict((re.escape(k), v) for k, v in replacements.items())
        self.pattern = re.compile("\\b(" + "|".join(escaped.keys()) + ")\\b")

    def __call__(self, utterance):
        return self.pattern.sub(lambda m: "<" + self.rep[m.group(0)] + ">", utterance)

    @staticmethod
    def from_knowledge_base(kb):
        # Room is a subtype of location, but we make an exception and anonymize it as "roomN"
        isroom = kb.attributes["location"]["isroom"]
        rooms = []
        for key, isroom in isroom.items():
            if isroom:
                rooms.append(key)
        return Anonymizer(kb.by_name["object"], kb.by_name["category"], kb.by_name["name"], kb.by_name["location"],
                          rooms, kb.by_name["gesture"])


class NumberingAnonymizer(Anonymizer):
    def __call__(self, utterance):
        type_count = defaultdict(lambda: 0)
        scrubbed = utterance
        for match in self.pattern.finditer(utterance):
            type = self.rep[match.group()]
            type_count[type] += 1

        num_type_anon_so_far = defaultdict(lambda: 0)
        while True:
            match = self.pattern.search(scrubbed)
            if not match:
                break
            string = match.groups()[0]
            replacement_type = self.rep[string]
            if type_count[replacement_type] > 1:
                current_num = num_type_anon_so_far[replacement_type] + 1
                replacement_string = "<" + self.rep[string] + " " + str(current_num) + ">"
                num_type_anon_so_far[replacement_type] += 1
            else:
                replacement_string = "<" + self.rep[string] + ">"
            scrubbed = scrubbed.replace(string, replacement_string, 1)

        return scrubbed
