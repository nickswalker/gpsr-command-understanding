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
        obfuscated_str = '?' if self.obfuscated else ""
        type_str = self.type if self.type else ""
        extra_str = self.id if self.id else ""
        if self.metadata:
            meta_members_as_str = list(map(str, self.metadata))
            meta_str = "meta: " + " ".join(meta_members_as_str)
        else:
            meta_str = ""
        return "Wildcard(" + '{} {} {} {} {}'.format(self.name, type_str, extra_str, obfuscated_str,
                                                     meta_str).strip() + ')'

    def to_human_readable(self):
        obfuscated_str = '?' if self.obfuscated else ""
        type_str = self.type if self.type else ""
        extra_str = self.id if self.id else ""
        if self.metadata:
            meta_members_as_str = list(map(str, self.metadata))
            meta_str = "meta: " + " ".join(meta_members_as_str)
        else:
            meta_str = ""
        return '{' + "{} {} {} {} {}".format(self.name, type_str, extra_str, obfuscated_str, meta_str).strip() + '}'

    def to_snake_case(self):
        items = [self.name]
        if self.type: items.append(self.type)
        if self.id: items.append(self.id)
        if self.obfuscated: items.append("?")
        return "_".join(map(str, items))

    def __hash__(self):
        return hash(self.__str__())
    def __eq__(self, other):
        return isinstance(other,
                          WildCard) and self.name == other.name and self.type == other.type and self.id == other.id and self.obfuscated == other.obfuscated


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
