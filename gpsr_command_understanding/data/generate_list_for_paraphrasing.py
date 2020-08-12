import os
import random
import csv

from gpsr_command_understanding.generator.generator import Generator
from gpsr_command_understanding.generator.grammar import tree_printer
from gpsr_command_understanding.generator.loading_helpers import load, GRAMMAR_YEAR_TO_MODULE
from gpsr_command_understanding.generator.tokens import ROOT_SYMBOL
from gpsr_command_understanding.util import chunker

seed = 0
rehprasings_per_hit = 6
groundings_per_parse = 1
hits_per_file = 100


def main():
    random_source = random.Random(seed)

    generator = Generator(None)
    load(generator, "gpsr", GRAMMAR_YEAR_TO_MODULE[2021])

    all = list(generator.generate(ROOT_SYMBOL, random_generator=random_source))
    # Throw away metadata
    [generator.extract_metadata(x) for x in all]
    all_examples = []
    grounded_examples = []
    for ungrounded in all:
        grounder = generator.generate_grounding_assignments(ungrounded, random_generator=random_source)
        for i in range(groundings_per_parse):
            assignment = next(grounder)
            grounded = generator.apply_grounding_assignment(ungrounded, assignment)
            # Remove unhelpful wildcards like pronouns
            for key in list(assignment.keys()):
                if "pron" in key.name:
                    del assignment[key]
            hint = ",".join(assignment.values())
            grounded_examples.append((grounded, ungrounded, hint))
    random_source.shuffle(grounded_examples)
    all_examples += grounded_examples


    command_columns = [("command" + str(x), "ungrounded" + str(x), "groundinghint"+str(x)) for x in
                       range(0, rehprasings_per_hit)]

    command_columns = [x for tuple in command_columns for x in tuple]
    command_columns.append("hitid")
    chunks = list(chunker(all_examples, rehprasings_per_hit))
    print("Writing {} HITS".format(len(chunks)))
    i = 0
    chunk_count = 0
    while i < len(chunks):
        out_file_path = os.path.abspath(
            os.path.dirname(__file__) + "/../../data/paraphrasing_input_{}.csv".format(chunk_count))
        with open(out_file_path, 'w') as csvfile:
            output = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            output.writerow(command_columns)

            for j in range(i, min(i + hits_per_file, len(chunks))):
                chunk = chunks[j]
                if len(chunk) < rehprasings_per_hit:
                    needed = rehprasings_per_hit - len(chunk)
                    # Sample from previous hits to fill out this last one
                    chunk += random_source.sample([pair for chunk in chunks[:i] for pair in chunk], k=needed)
                line = []
                for command, ungrounded, hint in chunk:
                    line += [tree_printer(command), tree_printer(ungrounded), hint]
                # HIT ID
                line.append(str(j))
                output.writerow(line)

            # Let's verify that we can load the output back in...
            with open(out_file_path, 'r') as csvfile:
                input = csv.DictReader(csvfile)
                for line in input:
                    pass
                    # print(line)
            i += hits_per_file
            chunk_count += 1


if __name__ == "__main__":
    main()
