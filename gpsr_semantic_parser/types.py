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
    """
    A nonterminal type representing some object, location, gesture, category, or name.
    Not fully modeled.
    """
    def __init__(self, name, type=None, extra=None, obfuscated=False):
        self.obfuscated = obfuscated
        self.type = type.strip() if type else None
        self.extra = extra.strip() if extra else None
        super(WildCard, self).__init__(name)
    def __str__(self):
        obfuscated_str = '?' if self.obfuscated else ""
        type_str = self.type if self.type else ""
        extra_str = self.extra if self.extra else ""
        return "Wildcard(" + '{} {} {}'.format(self.name, type_str, extra_str, obfuscated_str).strip() + ')'
    def to_human_readable(self):
        obfuscated_str = '?' if self.obfuscated else ""
        type_str = self.type if self.type else ""
        extra_str = self.extra if self.extra else ""
        return '{' + "{} {} {} {}".format(self.name, type_str, extra_str, obfuscated_str).strip() + '}'
    def __hash__(self):
        return hash(self.__str__())
    def __eq__(self, other):
        return isinstance(other, WildCard) and self.name == other.name and self.type == other.type and self.extra == other.extra and self.obfuscated == other.obfuscated


class Anonimized(object):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return "<{}>".format(self.name)
    def __hash__(self):
        return hash(self.__str__())
    def __eq__(self, other):
        return isinstance(other, Anonimized) and self.name == other.name


# The GPSR grammars all have this as their root
ROOT_SYMBOL = NonTerminal("Main")
