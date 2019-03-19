import json
import sys

def main(argv):
  if len(argv) != 3:
    print("Usage: python -m scripts.make_prediction_source input_file output_location")
    return

  input_file = argv[1]
  output_file = argv[2]

  fd = open(input_file, "r")
  input_lines = fd.readlines()
  fd.close()

  fd = open(output_file, "w")
  for i in range(len(input_lines)):
    if i % 2 == 0:
      line = input_lines[i]
      line = line.strip()
  
      res = {"source": line}
      res_str = json.dumps(res)
  
      fd.write(res_str + "\n")
  fd.close()
  

if __name__ == '__main__':
  main(sys.argv)
