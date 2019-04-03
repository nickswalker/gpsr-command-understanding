import operator

from gpsr_semantic_parser.types import TextFragment, BAR, L_PAREN, R_PAREN, Void, WildCard, NonTerminal


def merge_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z

def assert_no_wildcards(token_sequence):
    assert not any(isinstance(x, WildCard) or isinstance(x, NonTerminal) for x in token_sequence)

def tokens_to_str(tokens, show_void=False):
    output = ""
    for token in tokens:
        if isinstance(token, str):
            output += token + ' '
        elif isinstance(token, Void) and not show_void:
            continue
        else:
            to_str = token.to_human_readable()
            if to_str[0] == ',':
                output = output[:-1] + token.to_human_readable() + ' '
            else:
                output += token.to_human_readable() + ' '
    return output[:-1]


def productions_to_str(productions):
    output = ""
    for token, production in productions:
        output += token.to_human_readable() + " -> "+ tokens_to_str(production) + '\n'

    return output[:-1]


def combine_adjacent_text_fragments(tokens):
    """
    Grammars may generate multiple text fragments in a sequence. This will combine them
    :param tokens:
    :return: a list of tokens with no adjacent text fragments
    """
    cleaned = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        # Not a fragment? Forward to output
        if not isinstance(token, TextFragment):
            cleaned.append(token)
            i += 1
            continue
        elif token.text == "":
            i += 1
            continue
        # Otherwise, gather up the the next subsequence of fragments
        j = i + 1
        while j < len(tokens):
            next_token = tokens[j]
            if isinstance(next_token, TextFragment):
                j += 1
                continue
            break
        cleaned.append(TextFragment.join(tokens[i:j]))
        i = j
    if i == len(tokens) - 1:
        cleaned.append(tokens[i])
    return cleaned


def expand_shorthand(prefix_tokens, remaining_tokens, state, all_expansions):
    """
    The grammar allows a shorthand for specifying alternate productions
    This (is | will be | can be | should be) awesome ((someday | someday soon) | now)
    :param prefix_tokens:
    :param remaining_tokens:
    :param state:
    :param all_expansions:
    :return:
    """
    if len(remaining_tokens) == 0:
        all_expansions.append(prefix_tokens)
        return all_expansions
    for i, token in enumerate(remaining_tokens):
        if token == BAR:
            if state == "ALPH":
                all_expansions.append(prefix_tokens + remaining_tokens[0:i])
                return expand_shorthand(prefix_tokens, remaining_tokens[i + 1:], state, all_expansions)
            elif state == "PAREN_START":
                state_n = "PAREN_END"
                prefix_n = prefix_tokens + remaining_tokens[0:i]
                expand_shorthand(prefix_n, remaining_tokens[i + 1:], state_n, all_expansions)
                # start another branch for production B in (A | B | ...)
                return expand_shorthand(prefix_tokens, remaining_tokens[i + 1:], state, all_expansions)
            elif state == "PAREN_END":
                continue  # searching for )
        elif token == L_PAREN:
            state_n = "PAREN_START"
            prefix_n = prefix_tokens + remaining_tokens[0:i]
            return expand_shorthand(prefix_n, remaining_tokens[i + 1:], state_n, all_expansions)
        elif token == R_PAREN:
            if state == "PAREN_END":
                state = "ALPH"
                return expand_shorthand(prefix_tokens, remaining_tokens[i + 1:], state, all_expansions)
            elif state == "PAREN_START":
                state = "ALPH"
                prefix_n = prefix_tokens + remaining_tokens[0:i]
                return expand_shorthand(prefix_n, remaining_tokens[i + 1:], state, all_expansions)
    all_expansions.append(prefix_tokens + remaining_tokens)
    return all_expansions


class Counter(dict):
    """
    A counter keeps track of counts for a set of keys.
    The counter class is an extension of the standard python
    dictionary type.  It is specialized to have number values
    (integers or floats), and includes a handful of additional
    functions to ease the task of counting data.  In particular,
    all keys are defaulted to have value 0.  Using a dictionary:
    a = {}
    print a['test']
    would give an error, while the Counter class analogue:
    >>> a = Counter()
    >>> print a['test']
    0
    returns the default 0 value. Note that to reference a key
    that you know is contained in the counter,
    you can still use the dictionary syntax:
    >>> a = Counter()
    >>> a['test'] = 2
    >>> print a['test']
    2
    This is very useful for counting things without initializing their counts,
    see for example:
    >>> a['blah'] += 1
    >>> print a['blah']
    1
    The counter also includes additional functionality useful in implementing
    the classifiers for this assignment.  Two counters can be added,
    subtracted or multiplied together.  See below for details.  They can
    also be normalized and their total count and arg max can be extracted.
    """
    def __getitem__(self, idx):
        self.setdefault(idx, 0)
        return dict.__getitem__(self, idx)

    def incrementAll(self, keys, count):
        """
        Increments all elements of keys by the same count.
        >>> a = Counter()
        >>> a.incrementAll(['one','two', 'three'], 1)
        >>> a['one']
        1
        >>> a['two']
        1
        """
        for key in keys:
            self[key] += count

    def argMax(self):
        """
        Returns the key with the highest value.
        """
        if len(self.keys()) == 0: return None
        all = self.items()
        values = [x[1] for x in all]
        maxIndex = values.index(max(values))
        return all[maxIndex][0]

    def sortedKeys(self):
        """
        Returns a list of keys sorted by their values.  Keys
        with the highest values will appear first.
        >>> a = Counter()
        >>> a['first'] = -2
        >>> a['second'] = 4
        >>> a['third'] = 1
        >>> a.sortedKeys()
        ['second', 'third', 'first']
        """
        sortedItems = self.items()
        sortedItems = sorted(sortedItems, key=operator.itemgetter(1))
        return [x[0] for x in sortedItems]

    def totalCount(self):
        """
        Returns the sum of counts for all keys.
        """
        return sum(self.values())

    def normalize(self):
        """
        Edits the counter such that the total count of all
        keys sums to 1.  The ratio of counts for all keys
        will remain the same. Note that normalizing an empty
        Counter will result in an error.
        """
        total = float(self.totalCount())
        if total == 0: return
        for key in self.keys():
            self[key] = self[key] / total

    def divideAll(self, divisor):
        """
        Divides all counts by divisor
        """
        divisor = float(divisor)
        for key in self:
            self[key] /= divisor

    def copy(self):
        """
        Returns a copy of the counter
        """
        return Counter(dict.copy(self))

    def __mul__(self, y ):
        """
        Multiplying two counters gives the dot product of their vectors where
        each unique label is a vector element.
        >>> a = Counter()
        >>> b = Counter()
        >>> a['first'] = -2
        >>> a['second'] = 4
        >>> b['first'] = 3
        >>> b['second'] = 5
        >>> a['third'] = 1.5
        >>> a['fourth'] = 2.5
        >>> a * b
        14
        """
        sum = 0
        x = self
        if len(x) > len(y):
            x,y = y,x
        for key in x:
            if key not in y:
                continue
            sum += x[key] * y[key]
        return sum

    def __radd__(self, y):
        """
        Adding another counter to a counter increments the current counter
        by the values stored in the second counter.
        >>> a = Counter()
        >>> b = Counter()
        >>> a['first'] = -2
        >>> a['second'] = 4
        >>> b['first'] = 3
        >>> b['third'] = 1
        >>> a += b
        >>> a['first']
        1
        """
        for key, value in y.items():
            self[key] += value

    def __add__( self, y ):
        """
        Adding two counters gives a counter with the union of all keys and
        counts of the second added to counts of the first.
        >>> a = Counter()
        >>> b = Counter()
        >>> a['first'] = -2
        >>> a['second'] = 4
        >>> b['first'] = 3
        >>> b['third'] = 1
        >>> (a + b)['first']
        1
        """
        addend = Counter()
        for key in self:
            if key in y:
                addend[key] = self[key] + y[key]
            else:
                addend[key] = self[key]
        for key in y:
            if key in self:
                continue
            addend[key] = y[key]
        return addend

    def __sub__( self, y ):
        """
        Subtracting a counter from another gives a counter with the union of all keys and
        counts of the second subtracted from counts of the first.
        >>> a = Counter()
        >>> b = Counter()
        >>> a['first'] = -2
        >>> a['second'] = 4
        >>> b['first'] = 3
        >>> b['third'] = 1
        >>> (a - b)['first']
        -5
        """
        addend = Counter()
        for key in self:
            if key in y:
                addend[key] = self[key] - y[key]
            else:
                addend[key] = self[key]
        for key in y:
            if key in self:
                continue
            addend[key] = -1 * y[key]
        return addend


