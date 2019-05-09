import sys
import os

def main():

    f_in = open(sys.argv[1], 'r')
    f_name = sys.argv[1].split('.')[0]

    path_out = f_name

    if not os.path.exists(path_out):
        os.mkdir(path_out)

    seq_in = open(path_out + "/seq.in", "w")
    seq_out = open(path_out + "/seq.out", "w")
    label = open(path_out + "/label", "w")

    line = f_in.readline()
    while line:
        width = len(line) - len(line.lstrip()) - 1
        sentence_tokens = line.split()

        seq_in.write(" ".join(token for token in sentence_tokens) + "\n")

        line = f_in.readline().rstrip()
        parse_tokens = line.split()
        label.write(parse_tokens[0] + "\n")
        seq_out.write(" ".join(token for token in parse_tokens[1:]) + "\n")

        line = f_in.readline()


if __name__ == "__main__":
    main()