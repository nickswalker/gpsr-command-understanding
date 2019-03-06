from allennlp.common.testing import AllenNlpTestCase
from allennlp.common.util import ensure_list
from gpsr_semantic_parser.dataset_readers.seq2seq import Seq2SeqDatasetReader

class TestSeq2SeqReader(AllenNlpTestCase):

    def setUp(self):
        super(TestSeq2SeqReader, self).setUp()
        self.reader = Seq2SeqDatasetReader()
        instances = self.reader.read("fixtures/train.txt")
        self.instances = ensure_list(instances)

    def test_tokens(self):
        assert len(self.instances) == 7
