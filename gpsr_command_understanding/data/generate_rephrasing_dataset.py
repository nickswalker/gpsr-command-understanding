import os
import random
import csv

from gpsr_command_understanding.generator.grammar import tree_printer
from gpsr_command_understanding.generator.loading_helpers import load_paired_2018_by_cat, GRAMMAR_DIR_2018
from gpsr_command_understanding.util import chunker

seed = 0
rehprasings_per_hit = 12
groundings_per_parse = 1


def main():
    random_source = random.Random(seed)
    out_file_path = os.path.abspath(
        os.path.dirname(__file__) + "/../../data/rephrasings_data_{}_{}.csv".format(seed, groundings_per_parse))
    generator = load_paired_2018_by_cat(GRAMMAR_DIR_2018)

    all_examples = []
    for i in range(groundings_per_parse):
        # FIXME: Use the new grounding
        grounded_examples = None
        random_source.shuffle(grounded_examples)
        all_examples += grounded_examples

    with open(out_file_path, 'w') as csvfile:
        output = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        command_columns = [("command" + str(x), "parse" + str(x), "parse_ground" + str(x)) for x in
                           range(1, rehprasings_per_hit + 1)]
        command_columns = [x for tuple in command_columns for x in tuple]
        output.writerow(command_columns)

        chunks = list(chunker(all_examples, rehprasings_per_hit))
        print("Writing {} HITS".format(len(chunks)))
        for i, chunk in enumerate(chunks):
            if len(chunk) < rehprasings_per_hit:
                needed = rehprasings_per_hit - len(chunk)
                # Sample from previous hits to fill out this last one
                chunk += random_source.sample([pair for chunk in chunks[:i] for pair in chunk], k=needed)
            line = []
            for utterance, parse_anon, parse_ground in chunk:
                line += [tree_printer(utterance), tree_printer(parse_anon), tree_printer(parse_ground)]
            output.writerow(line)

    # Let's verify that we can load the output back in...
    with open(out_file_path, 'r') as csvfile:
        input = csv.DictReader(csvfile)
        for line in input:
            pass
            # print(line)


if __name__ == "__main__":
    main()
