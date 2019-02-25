import unittest

from gpsr_semantic_parser.semantics import parse_tokens
from gpsr_semantic_parser.types import String, Lambda


class TestSemanticsLoader(unittest.TestCase):
    def test(self):
        #parse_tokens([String("bare_variable")])
        parse_tokens([String("test"), '(', String("value"), ')'])
        parse_tokens([String("test"), '(', String("value"), ',', String("second"), ')'])
        parse_tokens([String("test"), '(', String("value"), ',', String("nested_pred"), '(', String("deep_value"), ')', ',', String("second"), ')'])
        parse_tokens([String("test"), '(', String("value"), ',', Lambda([],[],[]), '(', String("deep_value"), ')', ',', String("second"), ')'])