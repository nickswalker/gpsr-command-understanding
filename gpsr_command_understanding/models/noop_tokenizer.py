from typing import List

from overrides import overrides

from allennlp.data.tokenizers.token import Token
from allennlp.data.tokenizers.tokenizer import Tokenizer


@Tokenizer.register("no_op")
class NoOpTokenizer(Tokenizer):
    """
    Just returns the unsplit line. Helpful for reusing a datasetreader for just dumping lines out of a file
    """

    def __init__(self, ) -> None:
        pass

    @overrides
    def tokenize(self, text: str) -> List[Token]:
        """
        Does whatever processing is required to convert a string of text into a sequence of tokens.
        At a minimum, this uses a ``WordSplitter`` to split words into text.  It may also do
        stemming or stopword removal, depending on the parameters given to the constructor.
        """
        return [Token(text)]
