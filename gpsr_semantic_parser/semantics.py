from gpsr_semantic_parser.grammar import tokenize
from gpsr_semantic_parser.util import combine_adjacent_text_fragments, expand_shorthand, tokens_to_str
from gpsr_semantic_parser.types import String, Lambda, WildCard, Predicate, Constant, TYPED_LAMBDA_NAME_RE, L_PAREN, \
    R_PAREN, \
    L_C_BRACE, COMMA, WHITESPACE_RE, PRED_NAME_RE, WILDCARD_RE, SemanticTemplate, TemplateConstant, TemplatePredicate, \
    WILDCARD_ALIASES, NON_TERM_RE, DOLLAR, NonTerminal, LAMBDA_ARG_RE, Variable, BAR, R_C_BRACE
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
                names.append(int(name.replace(DOLLAR,'')))
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
            # We'll grab a string where the braces are balanced
            count = 1
            end_cursor = cursor + 1
            while count != 0:
                if raw_rule[end_cursor] == L_C_BRACE:
                    count += 1
                elif raw_rule[end_cursor] == R_C_BRACE:
                    count -= 1
                end_cursor += 1
            match = re.search(WILDCARD_RE, raw_rule[cursor:end_cursor])
            name = match.groupdict()["name"]

            if name in WILDCARD_ALIASES.keys():
                inner_string = match.group().replace(name, " ".join(WILDCARD_ALIASES[name]))
                match = re.search(WILDCARD_RE, inner_string)
            name = match.groupdict()["name"]
            type = match.groupdict()["type"]
            extra = match.groupdict()["extra"]
            obfuscated = match.groupdict()["obfuscated"] != None
            tokens.append(WildCard(name, type, extra, obfuscated))
            cursor = end_cursor
        elif char == COMMA:
            tokens.append(COMMA)
            cursor += 1
        elif char == DOLLAR:
            match = re.search(NON_TERM_RE, raw_rule[cursor:])
            if match:
                name = match.groupdict()["name"]
                tokens.append(NonTerminal(name))
            else:
                match = re.search(LAMBDA_ARG_RE, raw_rule[cursor:])
                name = int(match.groupdict()["name"])
                tokens.append(Variable(name))
            cursor += match.end()
        elif char == BAR:
            tokens.append(BAR)
            cursor += 1
        elif char.isspace():
            match = re.search(WHITESPACE_RE, raw_rule[cursor:])
            cursor += match.end()
        else:
            match = re.search(PRED_NAME_RE, raw_rule[cursor:])
            tokens.append(String(match.group()))
            if match.end() == 0:
                raise RuntimeError("couldn't parse starting at {}: {}".format(cursor, raw_rule))
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
            return TemplatePredicate(str(root), arg_tokens), i
        else:
            return Predicate(root.name, arg_tokens), i
    elif isinstance(root, Lambda):
        assert tokens[0] == L_PAREN
        parsed_arg, last_processed_index = parse_tokens_recursive(tokens[1], tokens[2:])
        # Pop off L_paren, contents, R_paren then move cursor one more to be at unseen token
        return Lambda(root.name, root.types, parsed_arg), 1 + last_processed_index + 2
    elif isinstance(root, WildCard):
        return TemplateConstant(str(root)), 1
    elif isinstance(root, String):
        # A string without parens is a  constant
        return Constant(root.name), 1
    elif isinstance(root, Variable):
        return Variable(root.name), 1
    elif isinstance(root, NonTerminal):
        #Todo: does this work?
        return TemplateConstant(str(root)), 1
    else:
        raise RuntimeError("Unexpected token")


def parse_tokens(tokens):
    if len(tokens) == 1:
        return tokens[0]
    try:
        parsed, last_parsed = parse_tokens_recursive(tokens[0], tokens[1:])
        if last_parsed != len(tokens):
            raise RuntimeError()
    except RuntimeError as e:
        print("Failed to parse: {}".format(tokens_to_str(tokens)))
        raise e

    return parsed


def parse_rule(line, rule_dict):
    prod, semantics = line.split("=")
    prod = tokenize(prod.strip())
    prod = combine_adjacent_text_fragments(prod)
    expanded_prod_heads = expand_shorthand([], prod, "ALPH", [])
    expanded_prod_heads = [combine_adjacent_text_fragments(x) for x in expanded_prod_heads]
    sem = semantics.strip()
    sem = tokenize_semantics(sem)

    for head in expanded_prod_heads:
        # Check for any obvious errors in the annotation
        for sem_token in sem:
            if isinstance(sem_token, WildCard) or isinstance(sem_token, NonTerminal):
                if sem_token not in head:
                    raise RuntimeError("Semantics rely on non-terminal {} that doesn't occur in rule: {}".format(sem_token, line))

        parsed_sem = parse_tokens(sem)
        rule_dict[tuple(head)] = SemanticTemplate(parsed_sem)


def load_semantics(semantics_file_paths):
    """
    :param semantics_file_paths:
    :return: dictionary mapping productions in grammar to semantics for planner
    """
    if isinstance(semantics_file_paths, str):
        semantics_file_paths = [semantics_file_paths]
    prod_to_semantics = {}
    for semantics_file_path in semantics_file_paths:
        with open(semantics_file_path) as f:
            for line in f:
                cleaned = line.strip()
                if len(cleaned) == 0 or cleaned[0] == '#':
                    continue
                parse_rule(cleaned, prod_to_semantics)

    return prod_to_semantics