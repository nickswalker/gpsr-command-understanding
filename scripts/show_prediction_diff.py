import json
import sys


def main(argv):
    if len(argv) != 4:
        print("Usage: python scripts/show_prediction_diff source file1 file2")
        return

    fd1 = open(argv[2], "r")
    lines1 = fd1.readlines()
    fd1.close()
    fd2 = open(argv[3], "r")
    lines2 = fd2.readlines()
    fd2.close()

    fs = open(argv[1], "r")
    linesSource = fs.readlines()
    fs.close()

    for i in range(len(lines1)):
        line1 = lines1[i]
        line2 = lines2[i]
        source = linesSource[i]

        tokens1 = json.loads(line1)["predicted_tokens"]
        tokens2 = json.loads(line2)["predicted_tokens"]
        input_data = json.loads(source)["source"]

        if tokens1 != tokens2:
            print("Input:", input_data)
            print("File1:", " ".join(tokens1))
            print("Files2:", " ".join(tokens2))
            print()

if __name__ == '__main__':
    main(sys.argv)
