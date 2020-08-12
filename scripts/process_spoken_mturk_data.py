import glob
import os
import re

import audioread as audioread
from nltk.metrics.distance import edit_distance, jaccard_distance
import pandas as pd
import hashlib

from nltk.tokenize import word_tokenize

paraphrasings = []
new = []


def get_file_duration(filename):
    with audioread.audio_open("saved_audio/" + filename) as f:
        return sum(map(len, f)) / f.samplerate / f.channels


def load_transcript(filename):
    path = "transcripts/" + filename
    if not os.path.isfile(path):
        return ""
    with open(path) as f:
        return f.readline().strip()


def clean_text(text):
    # split into words

    tokens = word_tokenize(text)
    # remove all tokens that are not alphabetic
    words = [word for word in tokens if word.isalpha()]
    return " ".join(words)


def process_turk_files(paths, filter_rejected=True):
    print("Processing paths: {}".format(str(paths)))

    def drop_trailing_num(name):
        try:
            return next(re.finditer(r'[\D\.]*', name)).group(0)
        except StopIteration:
            return name

    # Ignore index so that we get a new ID per row, instead of numbers by file
    frame = pd.concat([pd.read_csv(path, na_filter=False) for path in paths], ignore_index=True)
    if filter_rejected:
        frame.drop(frame[frame["AssignmentStatus"] == "Rejected"].index, inplace=True)
    frame.sort_values(by="Input.hitid", inplace=True, ignore_index=True)
    data_views = []
    # Count the occurences of Input.command. Sometimes we issue batches with different numbers
    num_commands = frame.filter(regex='^Input.command', axis=1).shape[1]
    for n in range(num_commands):
        columns = ["Input.command" + str(n), "Answer.paraphrase" + str(n), "WorkerId", "Input.hitid"]
        data_views.append(frame[columns].rename(columns=drop_trailing_num))
    paraphrases = pd.concat(data_views)
    # We loaded many different files. Some may not have as many command columns as others
    paraphrases.dropna(inplace=True)
    paraphrases["Answer.paraphrase"] = paraphrases["Answer.paraphrase"].str.lower().apply(clean_text)

    new_views = []
    num_new_commands = frame.filter(regex='^Answer.newcommand', axis=1).shape[1]
    for n in range(num_new_commands):
        new_views.append(
            frame[["Answer.newcommand" + str(n), "WorkerId", "Input.hitid"]].rename(columns=drop_trailing_num))
    new = pd.concat(new_views)
    new["Answer.newcommand"] = new["Answer.newcommand"].str.lower().apply(clean_text)
    # Drop all the extra input or answer fields except those you want to use for additional stats
    other_data = frame.drop(
        columns=[c for c in frame.columns if
                 ("Input" in c or "Answer" in c) and c != "Answer.comment" and c != "Input.hitid"])

    nice_names = {"Answer.paraphrase": "paraphrase", "Input.command": "command", "Answer.newcommand": "command",
                  "Input.hitid": "hitid"}
    paraphrases.rename(columns=nice_names, inplace=True)
    new.rename(columns=nice_names, inplace=True)
    other_data.rename(columns=nice_names, inplace=True)
    return paraphrases, new, other_data


def load_transcripts(data):
    data["commandhash"] = data["command"].apply(lambda command: hashlib.sha256(bytes(command, "utf-8")).hexdigest()[:6])
    data["filename"] = data["hitid"].astype(str) + "-" + data["commandhash"] + ".ogg"
    # paraphrases["duration"] = paraphrases["filename"].apply(get_file_duration)
    data["transcript_filename"] = data["hitid"].astype(str) + "-" + data["commandhash"] + ".txt"
    data["transcript"] = data["transcript_filename"].apply(load_transcript)


paraphrasings, new, other_data = process_turk_files(glob.glob("Batch_*.csv"))

load_transcripts(paraphrasings)
load_transcripts(new)

paraphrasings["EditDistanceNormalized"] = paraphrasings.apply(
    lambda row: edit_distance(row["command"], row["paraphrase"]) / len(row["command"]), axis=1)
paraphrasings["EditDistance"] = paraphrasings.apply(
    lambda row: edit_distance(row["command"], row["paraphrase"]), axis=1)
paraphrasings["JaccardDistance"] = paraphrasings.apply(
    lambda row: jaccard_distance(set(row["command"].split()), set(row["paraphrase"].split())), axis=1)

paraphrasings["TranscriptQuality"] = paraphrasings.apply(
    lambda row: min(1, edit_distance(row["paraphrase"], row["transcript"]) / max(len(row["transcript"]), 1)), axis=1)
print(
    "{:.2f} {:.2f} {:.2f}".format(paraphrasings["EditDistanceNormalized"].mean(), paraphrasings["EditDistance"].mean(),
                                  paraphrasings["JaccardDistance"].mean()))
by_worker = paraphrasings.groupby(paraphrasings["WorkerId"])
for name, group in by_worker:
    print(name)
    for i, (original, paraphrase) in group[["command", "paraphrase"]].iterrows():
        print(original)
        print(paraphrase)
        print("")

turker_performance = pd.DataFrame()
turker_performance["HITTime"] = other_data.groupby("WorkerId")["WorkTimeInSeconds"].mean()
turker_performance["MeanNormalizedEditDistance"] = paraphrasings.groupby("WorkerId")["EditDistanceNormalized"].mean()
turker_performance["MeanJaccardDistance"] = paraphrasings.groupby("WorkerId")["JaccardDistance"].mean()
turker_performance["MeanTranscriptQuality"] = paraphrasings.groupby("WorkerId")["TranscriptQuality"].mean()
turker_performance["HITIds"] = other_data.groupby("WorkerId")["hitid"].apply(lambda x: ','.join(map(str, x)))
turker_performance["Comment"] = other_data.groupby("WorkerId")["Answer.comment"].apply(lambda x: ','.join(x))

turker_performance.to_csv("turker_stats.txt", index=False)

for _, (original, paraphrase, edit, jaccard) in paraphrasings[
    ["command", "paraphrase", "EditDistance", "JaccardDistance"]].iterrows():  # noqa
    print(original)
    print(paraphrase)
    print("dist: ed{:.2f} ja{:.2f}".format(edit, jaccard))
    print("")

print("--------------")
new_by_worker = new.groupby(new["WorkerId"])
for name, group in new_by_worker:
    print(name)
    for custom_utt in group["command"]:
        print(custom_utt)
        print("")

print("{} workers provided {} paraphrases and {} new commands".format(len(by_worker), len(paraphrasings), len(new)))

rephrasings_dict = {}
with open("paraphrasings.txt", 'w') as outfile:
    for _, (utt, parse) in paraphrasings[["paraphrase", "command"]].sort_values(
            by="paraphrase").iterrows():
        outfile.write(utt + "\n")
        outfile.write(parse + "\n")
        rephrasings_dict[utt] = parse

with open("custom.txt", 'w') as outfile:
    for utt in new["command"].sort_values():
        outfile.write(utt + "\n")
