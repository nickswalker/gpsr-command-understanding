from overrides import overrides

from allennlp.common.util import JsonDict
from allennlp.data import Instance
from allennlp.predictors.predictor import Predictor


@Predictor.register('my_seq2seq')
class CommandParser(Predictor):
    """Predictor wrapper for the CommandParser"""
    @overrides
    def predict_json(self, json_dict: JsonDict) -> JsonDict:
        command = json_dict['command']
        instance = self._dataset_reader.text_to_instance(source_string=command)

        # label_dict will be like {0: "ACL", 1: "AI", ...}
        label_dict = self._model.vocab.get_index_to_token_vocabulary('labels')
        # Convert it to list ["ACL", "AI", ...]
        all_labels = [label_dict[i] for i in range(len(label_dict))]

        return {"instance": self.predict_instance(instance)}