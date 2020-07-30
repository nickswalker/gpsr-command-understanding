import glob
import re

from nltk.metrics.distance import edit_distance, jaccard_distance
import pandas as pd

paraphrasings = []
new = []


def process_turk_files(paths, filter_rejected=True):
    print("Processing paths: {}".format(str(paths)))

    def drop_trailing_num(name):
        try:
            return next(re.finditer(r'[\D\.]*', name)).group(0)
        except StopIteration:
            return name

    frame = pd.concat([pd.read_csv(path, na_filter=False) for path in paths])
    if filter_rejected:
        frame.drop(frame[frame["AssignmentStatus"] == "Rejected"].index, inplace=True)

    data_views = []
    for n in range(1, 13):
        columns = ["Input.command" + str(n), "Answer.utterance" + str(n), "Input.parse" + str(n),
                   "Input.parse_ground" + str(n), "WorkerId"]
        data_views.append(frame[columns].rename(columns=drop_trailing_num))
    rephrasings = pd.concat(data_views)
    rephrasings.sort_values(by="Answer.utterance", inplace=True)
    new_views = []
    for n in range(1, 3):
        new_views.append(frame[["Answer.custom" + str(n), "WorkerId"]].rename(columns=drop_trailing_num))
    new = pd.concat(new_views)
    new.sort_values(by="Answer.custom", inplace=True)
    other_data = frame.drop(
        columns=[c for c in frame.columns if ("Input" in c or "Answer" in c) and not (c == "Answer.comment")])
    return rephrasings, new, other_data


paraphrasings, new, other_data = process_turk_files(glob.glob("../data/raw_turk/batch_*.csv"))

paraphrasings["EditDistanceNormalized"] = paraphrasings.apply(
    lambda row: edit_distance(row["Input.command"], row["Answer.utterance"]) / len(row["Input.command"]), axis=1)
paraphrasings["EditDistance"] = paraphrasings.apply(
    lambda row: edit_distance(row["Input.command"], row["Answer.utterance"]), axis=1)
paraphrasings["JaccardDistance"] = paraphrasings.apply(
    lambda row: jaccard_distance(set(row["Input.command"].split()), set(row["Answer.utterance"].split())), axis=1)

print(
    "{:.2f} {:.2f} {:.2f}".format(paraphrasings["EditDistanceNormalized"].mean(), paraphrasings["EditDistance"].mean(),
                                  paraphrasings["JaccardDistance"].mean()))
by_worker = paraphrasings.groupby(paraphrasings["WorkerId"])
for name, group in by_worker:
    print(name)
    for i, (original, paraphrase) in group[["Input.command", "Answer.utterance"]].iterrows():
        print(original)
        print(paraphrase)
        print("")

turker_performance = pd.DataFrame()
turker_performance["HITTime"] = other_data.groupby("WorkerId")["WorkTimeInSeconds"].mean()
turker_performance["MeanNormalizedEditDistance"] = paraphrasings.groupby("WorkerId")["EditDistanceNormalized"].mean()
turker_performance["MeanJaccardDistance"] = paraphrasings.groupby("WorkerId")["JaccardDistance"].mean()
turker_performance["Comment"] = other_data.groupby("WorkerId")["Answer.comment"]
for _, (original, parse, paraphrase, edit, jaccard) in paraphrasings[
    ["Input.command", "Input.parse", "Answer.utterance", "EditDistance", "JaccardDistance"]].iterrows():  # noqa
    print(original)
    print(parse)
    print(paraphrase)
    print("dist: ed{:.2f} ja{:.2f}".format(edit, jaccard))
    print("")

print("--------------")
new_by_worker = new.groupby(new["WorkerId"])
for name, group in new_by_worker:
    print(name)
    for custom_utt in group["Answer.custom"]:
        print(custom_utt)
        print("")

print("{} workers provided {} rephrasings and {} new commands".format(len(by_worker), len(paraphrasings), len(new)))

rephrasings_dict = {}
with open("../data/paraphrasings.txt", 'w') as outfile:
    for _, (utt, parse) in paraphrasings[["Answer.utterance", "Input.parse"]].sort_values(
            by="Answer.utterance").iterrows():
        outfile.write(utt + "\n")
        outfile.write(parse + "\n")
        rephrasings_dict[utt] = parse

with open("../data/paraphrasings_grounded.txt", 'w') as outfile:
    for _, (utt, parse) in paraphrasings[["Answer.utterance", "Input.parse_ground"]].sort_values(
            by="Answer.utterance").iterrows():
        outfile.write(utt + "\n")
        outfile.write(parse + "\n")
        rephrasings_dict[utt] = parse

with open("../data/custom.txt", 'w') as outfile:
    for utt in new["Answer.custom"].sort_values():
        outfile.write(utt + "\n")
