from typing import List

from allennlp.common.util import JsonDict, sanitize
from allennlp.data import Instance
from allennlp.predictors.predictor import Predictor


@Predictor.register('command_parser')
class CommandParser(Predictor):
    """Predictor wrapper for the CommandParser"""

    def predict_instance(self, instance: Instance) -> JsonDict:
        outputs = self._model.forward_on_instance(instance)
        out_dict = sanitize(outputs)
        digest = " ".join(out_dict["predicted_tokens"])
        out_dict["digest"] = digest
        return out_dict

    def predict_batch_instance(self, instances: List[Instance]) -> List[JsonDict]:
        outputs = self._model.forward_on_instances(instances)
        out_dict = sanitize(outputs)
        for i, pred in enumerate(out_dict):
            digest = " ".join(out_dict[i]["predicted_tokens"])
            out_dict[i]["digest"] = digest
        return out_dict

    def _json_to_instance(self, json_dict: JsonDict) -> Instance:
        command = json_dict['command']
        return self._dataset_reader.text_to_instance(source_string=command)
