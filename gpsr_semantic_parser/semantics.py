from gpsr_semantic_parser.grammar import tokenize
from gpsr_semantic_parser.util import combine_adjacent_text_fragments
from gpsr_semantic_parser.types import String, Lambda, WildCard, Predicate, Constant, TYPED_LAMBDA_NAME_RE, L_PAREN, R_PAREN, \
    L_C_BRACE, COMMA, WHITESPACE_RE, PRED_NAME_RE, WILDCARD_RE, SemanticTemplate, TemplateConstant, TemplatePredicate, \
    WILDCARD_ALIASES, NON_TERM_RE, NON_TERM, NonTerminal
import re


def tokenize_semantics(raw_rule):
    tokens = []
    cursor = 0
    while cursor != len(raw_rule):
        char = raw_rule[cursor]
        match = re.search(TYPED_LAMBDA_NAME_RE, raw_rule[cursor:])
        if match:
            args = match.groupdict()["args"].split(',')
            names = []
            types = []
            for arg in args:
                name, type = arg.split(':')
                names.append(name)
                types.append(type)
            # We'll partially initialize to represent the token
            tokens.append(Lambda(names,types,None))
            cursor += match.end()
            continue
        if char == L_PAREN:
            tokens.append(L_PAREN)
            cursor += 1
        elif char == R_PAREN:
            tokens.append(R_PAREN)
            cursor += 1
        elif char == L_C_BRACE:
            match = re.search(WILDCARD_RE, raw_rule[cursor:])
            name = match.groupdict()["name"]
            obfuscated = match.groupdict()["obfuscated"] is not None
            name = WILDCARD_ALIASES.get(name, name)
            tokens.append(WildCard(name,obfuscated))
            cursor += match.end()
        elif char == COMMA:
            tokens.append(COMMA)
            cursor += 1
        elif char == NON_TERM:
            match = re.search(NON_TERM_RE, raw_rule[cursor:])
            name = match.groupdict()["name"]
            tokens.append(NonTerminal(name))
            cursor += match.end()
        elif char.isspace():
            match = re.search(WHITESPACE_RE, raw_rule[cursor:])
            cursor += match.end()
        else:
            match = re.search(PRED_NAME_RE, raw_rule[cursor:])
            tokens.append(String(match.group()))
            assert match.end() > 0
            cursor += match.end()

    return tokens


def parse_tokens_recursive(root, tokens):
    if (isinstance(root, String) or isinstance(root, WildCard))and tokens[0] == L_PAREN:
        arg_tokens = []
        i = 1
        while i < len(tokens) and tokens[i] != R_PAREN:
            if tokens[i] == COMMA:
                i += 1
                continue
            parsed_arg, last_processed_index = parse_tokens_recursive(tokens[i], tokens[i + 1:])
            arg_tokens.append(parsed_arg)
            i += last_processed_index
        # Pop off right paren
        i += 2
        if isinstance(root, WildCard):
            obfuscated_str = "?" if root.obfuscated else ""
            return TemplatePredicate(root.name + obfuscated_str, arg_tokens), i
        else:
            return Predicate(root.name, arg_tokens), i
    elif isinstance(root, Lambda):
        assert tokens[0] == L_PAREN
        parsed_arg, last_processed_index = parse_tokens_recursive(tokens[1], tokens[2:])
        # Pop off L_paren, contents, R_paren then move cursor one more to be at unseen token
        return Lambda(root.name, root.types, parsed_arg), 1 + last_processed_index + 2
    elif isinstance(root, WildCard):
        return TemplateConstant(root.name), 1
    elif isinstance(root, String):
        # A string without parens is a variable or constant
        return Constant(root.name), 1
    elif isinstance(root, NonTerminal):
        # TODO: Figure out how to implement nonterm substitution
        raise NotImplementedError()
    else:
        assert False


def parse_tokens(tokens):
    if len(tokens) == 1:
        return tokens[0]
    parsed, last_parsed = parse_tokens_recursive(tokens[0], tokens[1:])
    assert last_parsed == len(tokens)
    return parsed


def load_semantics(semantics_file_paths):
    """
    :param semantics_file_paths:
    :return: dictionary mapping productions in grammar to semantics for planner
    """
    prod_to_semantics = {}
    for semantics_file_path in semantics_file_paths:
        with open(semantics_file_path) as f:
            for line in f:
                cleaned = line.strip()
                if len(cleaned) == 0 or cleaned[0] == '#':
                    continue
                prod, semantics = cleaned.split("=")
                prod = tokenize(prod.strip())
                prod = combine_adjacent_text_fragments(prod)
                sem = semantics.strip()
                sem = tokenize_semantics(sem)
                parsed_sem = parse_tokens(sem)
                prod_to_semantics[tuple(prod)] = SemanticTemplate(parsed_sem)
    return prod_to_semantics