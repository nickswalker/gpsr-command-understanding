# coding: utf-8


class NonTerminal(object):
    def __init__(self, name):
        self.name = name

    def to_human_readable(self):
        return "$" + self.name

    def __str__(self):
        return "NonTerminal({})".format(self.name)

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        return isinstance(other, NonTerminal) and self.name == other.name


class WildCard(NonTerminal):
    def __init__(self, name):
        super(WildCard, self).__init__(name)

    def __str__(self):
        return "Wildcard({})".format(self.name)

    def to_human_readable(self):
        return "{" + self.name + "}"

    def to_snake_case(self):
        return "_".join(self.name.split(" "))


class ComplexWildCard(WildCard):
    """
    A nonterminal type representing some object, location, gesture, category, or name.
    """

    def __init__(self, name, type=None, wildcard_id=None, obfuscated=False, meta=None, conditions=None):
        self.obfuscated = obfuscated
        self.type = type.strip() if type else None
        self.id = wildcard_id
        self.metadata = meta
        self.conditions = conditions if conditions else []
        super(ComplexWildCard, self).__init__(name)

    def __str__(self):
        return "Wildcard(" + self.to_human_readable()[1:-1] + ')'

    def to_human_readable(self):
        obfuscated_str = '?' if self.obfuscated else None
        if self.metadata:
            meta_members_as_str = list(map(str, self.metadata))
            meta_str = "meta: " + " ".join(meta_members_as_str)
        else:
            meta_str = None
        if self.conditions:
            conditions_str = "where "
            for key, value in self.conditions.items():
                if isinstance(value, str):
                    conditions_str += "{}=\"{}\" ".format(key, value)
                else:
                    conditions_str += "{}={} ".format(key, value)
            conditions_str = conditions_str[:-1]
        else:
            conditions_str = None
        # Get the args in the right order as strings
        args_to_map = filter(lambda x: x is not None, [self.name, self.type, self.id, obfuscated_str, conditions_str, meta_str])
        args_str = map(str, args_to_map)
        return '{' + " ".join(args_str) + '}'

    def to_snake_case(self):
        obfuscated_str = '?' if self.obfuscated else None
        items = [self.name, self.type, self.id, obfuscated_str]
        items = filter(lambda x: x is not None, items)
        return "_".join(map(str, items))

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        return isinstance(other,
                          WildCard) and self.name == other.name and self.type == other.type and self.id == other.id and self.obfuscated == other.obfuscated and self.conditions == other.conditions


class Anonymized(object):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "<{}>".format(self.name)

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        return isinstance(other, Anonymized) and self.name == other.name


# The GPSR grammars all have this as their root
ROOT_SYMBOL = NonTerminal("Main")
