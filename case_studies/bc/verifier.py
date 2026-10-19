import os
import subprocess
import multiprocessing
import logging
import argparse
from datetime import datetime
import functools

MODEL_DIR = "BC_SESSION_MODELS"  # the path of models
OUTPUT_DIR = "result"
CONTINUE_LAST_VERIFICATION = False

# Number of models verified at the same time. Nothing bounds the memory of a
# single tamarin-prover invocation, so peak memory is roughly this number times
# the peak of one model; lower it with --jobs if memory is tight.
PROCESSES = 16

# verifying the model
def verify(model, output_dir):
    model_name = os.path.basename(model)
    os.makedirs(output_dir, exist_ok=True)
    outfile = os.path.join(output_dir, f"{model_name}") # the file of output
    temp_file = f"{outfile}.tmp"

    if os.path.exists(outfile):
        return

    try:
        # Document the model that is working on 
        logging.info(f"Verifying model: {model_name}")
        print(f"Verifying model: {model_name}")

        # construct the command
        command = [
            "tamarin-prover",
            "+RTS", "-N8", "-RTS",
            "--stop-on-trace=SEQDFS",
            "--derivcheck-timeout=0",
            model,
            "--prove",
            f"--output={outfile}"
        ]

        # execute the command
        with open(temp_file, 'w') as temp:
            result = subprocess.run(command, stdout=temp, stderr=subprocess.PIPE)

        # check the result
        if result.returncode == 0:
            logging.info(f"Successfully verify {model_name}")
            print(f"Successfully verify {model_name}")  # print the information of success
            
            # write the result to outfile
            with open(outfile, 'a') as out:
                out.write("\n")
                with open(temp_file, 'r') as temp:
                    out.write(temp.read())
        else:
            logging.error(f"Error verifying {model_name}")
            print(f"Error verifying {model_name}: {result.stderr.decode()}")  # print the error
    
    except Exception as e:
        logging.error(f"Unexpected error verifying {model_name}")
        print(f"Unexpected error verifying {model_name}: {str(e)}")  # print the unexpected error
    
    finally:
        # remove the tempfile
        if os.path.exists(temp_file):
            os.remove(temp_file)

def main():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if CONTINUE_LAST_VERIFICATION:
        result_dirs = [d for d in os.listdir() if os.path.isdir(d) and d.startswith(OUTPUT_DIR)]
        if len(result_dirs) > 0:
            last_result_dir = sorted(result_dirs)[-1]
            timestamp = "_".join(last_result_dir.split("_")[1:])

    # the setting of log
    log_filename = f"verifier_{timestamp}.log"
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_filename)
        ]
    )

    # create the output file
    global OUTPUT_DIR
    OUTPUT_DIR = f"{OUTPUT_DIR}_{timestamp}"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # lterate through all the files int the directory
    def is_model_file(f:str): 
        return os.path.isfile(f) and f.endswith(".spthy")
    models = [f for f in os.listdir(MODEL_DIR) if is_model_file(os.path.join(MODEL_DIR, f))]
    models.sort()

    # Create a process pool and work with the model
    logging.info("Start verify")
    with multiprocessing.Pool(processes=PROCESSES) as pool:
        worker = functools.partial(verify, output_dir=OUTPUT_DIR)   
        pool.map(worker, [os.path.join(MODEL_DIR, m) for m in models])
    logging.info("Verify end")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="verification tool")
    parser.add_argument('--continue', dest='continue_flag', action='store_true')
    parser.add_argument('-j', '--jobs', dest='jobs', type=int, default=PROCESSES,
                        help=f"models to verify in parallel (default: {PROCESSES}). "
                             "Peak memory scales with this number.")
    args = parser.parse_args()

    CONTINUE_LAST_VERIFICATION = args.continue_flag
    if args.jobs < 1:
        parser.error("--jobs must be >= 1")
    PROCESSES = args.jobs

    main()
