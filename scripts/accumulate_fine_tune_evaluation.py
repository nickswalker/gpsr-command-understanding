import json
import sys
from os.path import join

models = [
    "bert_base_seq2seq",
    "bert_large_seq2seq",
    "elmo_seq2seq",
    "openai_seq2seq",
    "seq2seq"
]

iterations = [str(i) for i in range(1,18)] + ["Full"]

def main(argv):
    if len(argv) != 2:
        print("Usage: python -m scripts.accumulate_fine_tune_evaluation dir")
        return

    directory = argv[1]
    for model in models:
        seq_acc = []
        BLEU = []
        loss = []
        for iteration in iterations:
            path = join(directory, model + "_" + iteration + ".json")
            fd = open(path, "r")
            json_data = json.loads(fd.read())
            fd.close()
            seq_acc.append(json_data["seq_acc"])
            BLEU.append(json_data["BLEU"])
            loss.append(json_data["loss"])
        fd = open("fine_tune_evaluation_acc.json", "a+")
        fd.write(json.dumps({"model_name": model, "seq_acc": seq_acc, "BLEU": BLEU, "loss": loss}) + "\n")
        fd.close()

if __name__ == '__main__':
    main(sys.argv)
