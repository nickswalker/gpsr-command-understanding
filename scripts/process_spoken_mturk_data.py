import glob
import re

import audioread as audioread
from nltk.metrics.distance import edit_distance, jaccard_distance
import pandas as pd
import hashlib
import contextlib

from tinytag import TinyTag

paraphrasings = []
new = []

def get_file_duration(filename):
    with audioread.audio_open("saved_audio/"+ filename) as f:
        return sum(map(len, f)) / f.samplerate / f.channels

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
    for n in range(5):
        columns = ["Input.command" + str(n), "Answer.paraphrase" + str(n), "WorkerId", "Input.hitid"]
        data_views.append(frame[columns].rename(columns=drop_trailing_num))
    paraphrases = pd.concat(data_views)
    paraphrases.sort_values(by="Answer.paraphrase", inplace=True)
    paraphrases["commandhash"] = paraphrases["Input.command"].apply(lambda command: hashlib.sha256(bytes(command, "utf-8")).hexdigest()[:6])
    paraphrases["filename"] = paraphrases["Input.hitid"].astype(str) + "-" + paraphrases["commandhash"] + ".ogg"
    #paraphrases["duration"] = paraphrases["filename"].apply(get_file_duration)
    new_views = []
    for n in range(1):
        new_views.append(frame[["Answer.newcommand" + str(n), "WorkerId"]].rename(columns=drop_trailing_num))
    new = pd.concat(new_views)
    new.sort_values(by="Answer.newcommand", inplace=True)
    other_data = frame.drop(
        columns=[c for c in frame.columns if ("Input" in c or "Answer" in c) and not (c == "Answer.comment")])
    return paraphrases, new, other_data


paraphrasings, new, other_data = process_turk_files(glob.glob("Batch_*.csv"))

paraphrasings["EditDistanceNormalized"] = paraphrasings.apply(
    lambda row: edit_distance(row["Input.command"], row["Answer.paraphrase"]) / len(row["Input.command"]), axis=1)
paraphrasings["EditDistance"] = paraphrasings.apply(
    lambda row: edit_distance(row["Input.command"], row["Answer.paraphrase"]), axis=1)
paraphrasings["JaccardDistance"] = paraphrasings.apply(
    lambda row: jaccard_distance(set(row["Input.command"].split()), set(row["Answer.paraphrase"].split())), axis=1)

print(
    "{:.2f} {:.2f} {:.2f}".format(paraphrasings["EditDistanceNormalized"].mean(), paraphrasings["EditDistance"].mean(),
                                  paraphrasings["JaccardDistance"].mean()))
by_worker = paraphrasings.groupby(paraphrasings["WorkerId"])
for name, group in by_worker:
    print(name)
    for i, (original, paraphrase) in group[["Input.command", "Answer.paraphrase"]].iterrows():
        print(original)
        print(paraphrase)
        print("")

turker_performance = pd.DataFrame()
turker_performance["HITTime"] = other_data.groupby("WorkerId")["WorkTimeInSeconds"].mean()
turker_performance["MeanNormalizedEditDistance"] = paraphrasings.groupby("WorkerId")["EditDistanceNormalized"].mean()
turker_performance["MeanJaccardDistance"] = paraphrasings.groupby("WorkerId")["JaccardDistance"].mean()
turker_performance["Comment"] = other_data.groupby("WorkerId")["Answer.comment"].apply(lambda x: ','.join(x))

turker_performance.to_csv("turker_stats.txt", index=False)

for _, (original, paraphrase, edit, jaccard) in paraphrasings[
    ["Input.command", "Answer.paraphrase", "EditDistance", "JaccardDistance"]].iterrows():  # noqa
    print(original)
    print(paraphrase)
    print("dist: ed{:.2f} ja{:.2f}".format(edit, jaccard))
    print("")

print("--------------")
new_by_worker = new.groupby(new["WorkerId"])
for name, group in new_by_worker:
    print(name)
    for custom_utt in group["Answer.newcommand"]:
        print(custom_utt)
        print("")

print("{} workers provided {} paraphrases and {} new commands".format(len(by_worker), len(paraphrasings), len(new)))

rephrasings_dict = {}
with open("paraphrasings.txt", 'w') as outfile:
    for _, (utt, parse) in paraphrasings[["Answer.paraphrase", "Input.command"]].sort_values(
            by="Answer.paraphrase").iterrows():
        outfile.write(utt + "\n")
        outfile.write(parse + "\n")
        rephrasings_dict[utt] = parse


with open("custom.txt", 'w') as outfile:
    for utt in new["Answer.newcommand"].sort_values():
        outfile.write(utt + "\n")
