import re

from nltk.metrics.distance import edit_distance, jaccard_distance
import pandas as pd
rephrasings = []
new = []


def process_turk_file(path):
    def drop_trailing_num(name):
        try:
            return next(re.finditer(r'[\D\.]*',name)).group(0)
        except:
            return name

    frame = pd.read_csv(path)
    data_views = []
    for n in range(1, 13):
        columns = ["Input.command" + str(n),"Answer.utterance" + str(n), "Input.parse" + str(n), "Input.parse_ground" + str(n),  "WorkerId"]
        data_views.append(frame[columns].rename(columns=drop_trailing_num))
    rephrasings = pd.concat(data_views)
    new_views = []
    for n in range(1, 3):
        new_views.append(frame[["Answer.custom" + str(n), "WorkerId"]].rename(columns=drop_trailing_num))
    new = pd.concat(new_views)
    other_data = frame.drop(columns=[ c for c in frame.columns if "Input" in c or "Answer" in c])
    return rephrasings, new, other_data


rephrasings, new, other_data = process_turk_file("../data/test_hit_2.csv")

rephrasings["EditDistance"] = rephrasings.apply(lambda row: edit_distance(row["Input.command"],row["Answer.utterance"]) / len(row["Input.command"]), axis=1)
rephrasings["JaccardDistance"] = rephrasings.apply(lambda row: jaccard_distance(set(row["Input.command"].split(" ")),set(row["Answer.utterance"].split(" "))), axis=1)
rephrasings["BLEU"] = rephrasings.apply(lambda row: jaccard_distance(set(row["Input.command"].split(" ")),set(row["Answer.utterance"].split(" "))), axis=1)

by_worker = rephrasings.groupby(rephrasings["WorkerId"])
for name, group in by_worker:
    print(name)
    for i, (original, rephrasing) in group[["Input.command", "Answer.utterance"]].iterrows():
        print(original)
        print(rephrasing)
        print("")

turker_performance = pd.DataFrame()
turker_performance["HITTime"] = other_data.groupby("WorkerId")["WorkTimeInSeconds"].mean()
turker_performance["MeanEditDistance"] = rephrasings.groupby("WorkerId")["EditDistance"].mean()
turker_performance["MeanJaccardDistance"] = rephrasings.groupby("WorkerId")["JaccardDistance"].mean()
for _, (original, parse, rephrasing, edit, jaccard) in rephrasings[["Input.command","Input.parse","Answer.utterance", "EditDistance","JaccardDistance"]].iterrows():
    print(original)
    print(parse)
    print(rephrasing)
    print("dist: ed{:.2f} ja{:.2f}".format(edit, jaccard))
    print("")


print("--------------")
new_by_worker = new.groupby(new["WorkerId"])
for name, group in new_by_worker:
    print(name)
    for custom in group["Answer.custom"]:
        print(custom)
        print("")