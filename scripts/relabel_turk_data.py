import sys


def main():
    f_in = open(sys.argv[1], 'r')
    f_name = sys.argv[1].split('.')[0]

    f_out = open(f_name + "_slot.txt", "w")

    line = f_in.readline()
    while line:
        # f_out.write(line + "\n\n")
        line = line.replace(",", " ,")
        line = line.replace(". ", " . ")
        sentence_tokens = line.split(" ")
        sentence_str = " ".ljust(17) + " ".join(token.ljust(16) for token in sentence_tokens)
        f_out.write(sentence_str + "\n")

        line = f_in.readline()
        line = f_in.readline()


if __name__ == "__main__":
    main()
