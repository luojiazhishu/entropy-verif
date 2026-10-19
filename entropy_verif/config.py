import os

abs_path = os.path.dirname(os.path.abspath(__file__))

PASER_LIB = os.path.join(abs_path, "lib/build/libtamarin.so")

MODEL_CRACK_FILE = os.path.join(abs_path, "assets/low_entropy_crack.spthy")
MODEL_FUNCTIONS_FILE = os.path.join(abs_path, "assets/functions_equations.spthy")
