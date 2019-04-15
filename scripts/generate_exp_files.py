import json

models = [
    "bert_base_seq2seq",
    "bert_large_seq2seq",
    "elmo_seq2seq",
    "openai_seq2seq",
    "glove_seq2seq",
    "seq2seq"
]

labels = [str(i) for i in range(1, 9)] + ["Full"]

def main():
    for model in models:
        print(model)
        fd = open("experiments/{}.json".format(model), 'r')
        json_data = json.loads(fd.read())
        fd.close()
        json_data["validation_data_path"] = "data/2_2/val.txt"

        for label in labels:
            train_label = label
            if label == "Full":
                train_label = ""

            json_data["train_data_path"] = "data/2_2/train{}.txt".format(train_label)
            fd = open("experiments/{}_{}.json".format(model, label), 'w')
            fd.write(json.dumps(json_data))
            fd.close()

if __name__ == '__main__':
    main()
