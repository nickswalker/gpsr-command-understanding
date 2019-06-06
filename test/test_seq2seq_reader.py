import os
from os.path import join

from allennlp.common.testing import AllenNlpTestCase
from allennlp.common.util import ensure_list
from gpsr_command_understanding.models.seq2seq_data_reader import Seq2SeqDatasetReader


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

class TestSeq2SeqReader(AllenNlpTestCase):

    def setUp(self):
        super(TestSeq2SeqReader, self).setUp()
        self.reader = Seq2SeqDatasetReader()
        instances = self.reader.read(join(FIXTURE_DIR,"train.txt"))
        self.instances = ensure_list(instances)

    def test_tokens(self):
        self.assertEqual(len(self.instances), 9)
