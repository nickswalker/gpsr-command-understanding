from copy import deepcopy

from gpsr_command_understanding.util import replace_child, to_num

from gpsr_command_understanding.generator.tokens import *

from lark import Tree, Transformer, Visitor


class TypeConverter(Transformer):
    """
    Tree post-processor which takes Lark grammar rules as hints to wrap up
    special types of terminals
    """
    def bare_choice(self, children):
        return Tree("choice", children)
    def top_expression(self, children):
        # Bake the top expression down
        if len(children) == 1 and isinstance(children[0], Tree) and children[0].data == "expression":
            return children[0]
        return Tree("expression", children)

    def non_terminal(self, children):
        return NonTerminal(children[0])

    def wildcard(self, children):
        # We bundle expected args into the first child via the typed wildcard branches of the grammar
        typed = children[0]
        meta = None
        wildcard_id = None
        conditions = None
        obfuscated = False
        for child in children[1:]:
            if isinstance(child, str) and to_num(child):
                wildcard_id = to_num(children[1])
            elif isinstance(child, Tree):
                if child.data == "condition":
                    conditions = child.children
                elif child.data == "meta":
                    meta = child.children
                elif child == "?":
                    obfuscated = True

        # only a few kinds of wildcards can be obfuscated
        obfuscated = True if len(typed.children) > 0 and typed.children[-1] == "?" else False
        type = None
        if "object_" in typed.data:
            if "alike" in typed.data:
                type = "alike"
            elif "known" in typed.data:
                type = "known"
            return ComplexWildCard("object", type, obfuscated=obfuscated, wildcard_id=wildcard_id, meta=meta,
                                   conditions=conditions)
        elif "loc" in typed.data:
            # the type token (e.g. placement) is elided from the tree, so the extra
            # will be the only element in this list
            extra = typed.children[0] if len(typed.children) > 0 else None
            if "beacon" in typed.data:
                type = "beacon"
            elif "placement" in typed.data:
                type ="placement"
            elif "room" in typed.data:
                type = "room"
            return ComplexWildCard("location", type, obfuscated=obfuscated, wildcard_id=wildcard_id, meta=meta,
                                   conditions=conditions)
        elif "category" in typed.data:
            return ComplexWildCard("category", type, obfuscated=obfuscated, wildcard_id=wildcard_id, meta=meta,
                                   conditions=conditions)
        elif "gesture" in typed.data:
            return ComplexWildCard("gesture", type, wildcard_id=wildcard_id, meta=meta, conditions=conditions)
        elif "name" in typed.data:
            return ComplexWildCard("name", type, wildcard_id=wildcard_id, meta=meta, conditions=conditions)
        elif "pron" in typed.data:
            if "pronoun_objective" == typed.data:
                return WildCard("pron")
            elif "pronoun_subjective" == typed.data:
                return WildCard("pron sub")
            elif "pronoun_possessive_adjective" == typed.data:
                return WildCard("pron paj")
            elif "pronoun_possessive_absolute" == typed.data:
                return WildCard("pron pabs")
            else:
                assert False
        elif "question" in typed.data:
            return ComplexWildCard("question", type, wildcard_id=wildcard_id, meta=meta, conditions=conditions)
        elif "void" in typed.data:

            return ComplexWildCard("void", type, wildcard_id=wildcard_id, meta=meta, conditions=conditions)
        elif "whattosay" in typed.data:
            return ComplexWildCard("whattosay", wildcard_id=wildcard_id, meta=meta, conditions=conditions)
        assert False


class DiscardVoid(Visitor):
    """
    Throw away generator annotations meant for the referee
    """
    def expression(self, tree):
        tree.children = list(filter(lambda x: not ((isinstance(x, WildCard) or isinstance(x, Anonymized)) and x.name == "void"), tree.children))


class DiscardMeta(Visitor):
    """
    Throw away generator annotations meant for the referee
    """
    def expression(self, tree):
        for child in tree.children:
            if isinstance(child, ComplexWildCard):
                child.metadata = None


class RemovePrefix(Visitor):
    """
    Remove an arbitrary string that may appear at the beginning
    of subtree names
    """

    def __init__(self, prefix):
        self.prefix = prefix

    def __default__(self, tree):
        if tree.data.startswith(self.prefix):
            tree.data = tree.data[len(self.prefix):]


class CompactUnderscorePrefixed(Transformer):
    """
    Collapse nodes that start with an underscore
    """

    def __default__(self, data, children, meta):
        if data[0] == "_" and len(children) == 1:
            return children[0]
        return Tree(data, children, meta)


# TODO(nickswalker): Test this
class ToString(Transformer):
    def __default__(self, data, children, meta):
        as_str = ""
        for child in children:
            if isinstance(child, WildCard):
                as_str += " " + child.to_human_readable()
            elif isinstance(child, NonTerminal):
                as_str += " " + child.to_human_readable()
            else:
                as_str += " " + str(child)
        return as_str[1:]

    def non_terminal(self, children):
        return "${}".format(" ".join(children))

    def choice(self, children):
        output = "("
        for child in children:
            output += child + " | "
        return output[:-3] + ")"

    def rule(self, children):
        return "{} = {}".format(children[0], children[1])

    def predicate(self, children):
        # Check for any string constant args and make sure they have
        # padding spaces between text and the quote marks
        for i, child in enumerate(children):
            if isinstance(child, str) and child[0] == "\"" and child[1] != " ":
                children[i] = "\" " + child[1:-1] + " \""
        return "( {} )".format(self.__default__(None, children, None))

    def lambda_abs(self, children):
        return "( lambda {} )".format(" ".join(map(str, children)))

    def constant_placeholder(self, children):
        return "\"" + " ".join(children) + "\""

    def __call__(self, *args, **kwargs):
        return self.transform(*args)


tree_printer = ToString()


class CombineExpressions(Visitor):
    """
    Grammars may generate multiple text fragments in a sequence. This will combine them
    :param tokens:
    :return: a list of tokens with no adjacent text fragments
    """
    def top_expression(self, tree):
        tree.data = "expression"
        self.expression(tree)

    def expression(self, tree):
        cleaned = []
        i = 0
        while i < len(tree.children):
            child = tree.children[i]
            # Not a fragment? Forward to output
            if not (isinstance(child, Tree) and child.data == "expression"):
                cleaned.append(child)
                i += 1
                continue
            # Otherwise, gather up the the next subsequence of fragments
            j = i + 1
            while j < len(tree.children):
                next_child = tree.children[j]
                if isinstance(next_child, Tree) and next_child.data == "expression":
                    j += 1
                    continue
                break
            cleaned.extend([c for t in tree.children[i:j] for c in t.children])
            i = j
        if i == len(tree.children) - 1:
            cleaned.append(tree.children[i])

        all_expanded = False
        while not all_expanded:
            i = 0
            while i < len(cleaned):
                child = cleaned[i]
                if isinstance(child, Tree) and child.data == "expression":
                    cleaned = cleaned[:i] + child.children + cleaned[i+1:]
                    break
                i += 1
            all_expanded = True
        tree.children = cleaned


def expand_shorthand(tree):
    """
    A choice in a rule can be expanded into several different rules enumerating each combination of branch selections.
    This makes each choice and returns the list of resulting expressions
    :param tree:
    :return:
    """
    in_progress = [tree]
    output = []
    combiner = CombineExpressions()
    while len(in_progress) != 0:
        current = in_progress.pop()
        choice = None
        # Find the unmade choice that's furthest up the tree
        for subtree in current.iter_subtrees_topdown():
            if subtree.data == "choice":
                choice = subtree
                break
        if not choice:
            # All choices expanded!
            # Choices will make a mess of unnecessarily nested expressions. Clean
            # up.
            combiner.visit(current)
            output.append(current)
            continue
       # Make the choice in every way
        for option in choice.children:
            choice_made_tree = deepcopy(current)
            # Is this choice the root of the tree? No parent in this case
            if choice_made_tree == choice:
                in_progress.append(option)
            else:
                choice_parent = list(choice_made_tree.find_pred(lambda subtree: any([child == choice for child in subtree.children])))[0]
                replace_child(choice_parent, choice, option, only_once=True)
                in_progress.append(choice_made_tree)

    return output


def make_anonymized_grounding_rules(wildcards, show_details=False):
    """
    Generates a single special-token substitution for each wildcard.
    :param wildcards:
    :return:
    """
    grounding_rules = {}
    for wildcard in wildcards:
        if show_details:
            prod = Anonymized(wildcard.to_human_readable())
        else:
            # Room is an exception; it's disjoint with location
            if wildcard.type and wildcard.type == "room":
                prod = Anonymized("room")
            else:
                prod = Anonymized(wildcard.name)
        grounding_rules[wildcard] = [Tree("expression", [prod])]
    return grounding_rules


def rule_dict_to_str(rules):
    out = ""
    for non_term, productions in rules.items():
        out += non_term.to_human_readable() + "\n"
        for production in productions:
            out += "\t" + tree_printer(production) + "\n"
    return out
