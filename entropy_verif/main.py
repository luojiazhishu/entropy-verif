import os
import time
import shutil
import argparse
import itertools
from analyser import SyntaxData, SyntaxAnalyser
from config import MODEL_CRACK_FILE, MODEL_FUNCTIONS_FILE, PASER_LIB


def create_restrictions(name:str, level:int):
    restriction = f"restriction Crack{name}{level}Times:\n"
    restriction += f"    \"All x"
    for i in range(level+1):
        restriction += f" #i{i}"
    restriction += f". "
    for i in range(level+1):
        restriction += f"Crack{name}V(x)@#i{i} "
        if i < level:
            restriction += "& "
    restriction += f"\n        ==> "
    pairs = list(itertools.combinations(range(level+1), 2))
    for i in range(len(pairs)):
        restriction += f"#i{pairs[i][0]} = #i{pairs[i][1]}"
        if i < len(pairs) - 1:
            restriction += " | "
    restriction += "\"\n"
    return restriction


def add_restrictions_to_crack_model(crack_file, new_file, derive_level, propagate_level):
    with open(crack_file, 'r') as f:
        data = f.read()
    restriction1 = create_restrictions("Derive", derive_level)
    restriction2 = create_restrictions("Propagate", propagate_level)
    restrictions = f"#{{{restriction1}\n{restriction2}#}}"
    data = data.replace("end", restrictions)
    data += "\nend"
    with open(new_file, 'w') as f:
        f.write(data)
    return 


def main():
    global MODEL_CRACK_FILE

    parser = argparse.ArgumentParser()
    parser.add_argument('input', metavar='input_file', type=str, help='Input file name')
    parser.add_argument('-o', '--output', metavar='output_file', type=str,
                        default='out.spthy', help='Output file name (default: out.spthy)')
    parser.add_argument('--derive-level', type=int, default=3, help='Set the derive level (default: 3).')
    parser.add_argument('--propagate-level', type=int, default=3, help='Set the propagate level (default: 3).')


    args = parser.parse_args()

    input_filename = args.input
    output_filename = args.output
    d_level = args.derive_level
    p_level = args.propagate_level

    tmp_crack_file = f"/tmp/{os.getpid()}_crack.spthy"
    add_restrictions_to_crack_model(MODEL_CRACK_FILE, tmp_crack_file, d_level, p_level)

    begin = time.time()
    data = SyntaxData(file=input_filename)
    analyser = SyntaxAnalyser(data)
    new_data = analyser.generate_entropy_theory([MODEL_FUNCTIONS_FILE, tmp_crack_file])
    with open(output_filename, 'w') as f:
        f.write(new_data.build_code())
    print(f"Time consumed: {time.time() - begin:.2f}s")

    os.remove(tmp_crack_file)

if __name__ == '__main__':
    main()
