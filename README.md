## EntropyVerif

### Repository Structure

```
./EntropyVerif/
├── README.md       # this file
├── docker          # Dockerfiles for the two verification environments
├── case_studies    # models, scripts and results for case studies
│   ├── bc          # BC case study
│   ├── ble         # BLE case study
│   ├── pay         # pay case study
│   └── wpa2        # WPA2-PSK case study
└── entropy_verif   # source code of EntropyVerif
```

### Environment

All dependencies (`tamarin-prover`, `maude`, `graphviz`, Python 3 and the
C toolchain) are provided by Docker images built from `docker/`. Two images are
needed: the case studies were verified with different tamarin-prover versions.

| Image | tamarin-prover | Maude | Python | Case studies |
| --- | --- | --- | --- | --- |
| `entropyverif:1.8` | 1.8.0 | 2.7.1 | 3.12 | `bc`, `ble`, `wpa2` |
| `entropyverif:1.10` | 1.10.0 | 3.1 | 3.12 | `pay` |

Build them from the repository root. 

```bash
docker build -t entropyverif:1.8  -f docker/Dockerfile.tamarin1.8  docker/
docker build -t entropyverif:1.10 -f docker/Dockerfile.tamarin1.10 docker/
```

Every section below starts with a `docker run` line, to be run on the host from
the repository root. It mounts the repository at `/workspace` and opens a shell
there; the commands after it are run in that shell.

### Compile Library

Before using `EntropyVerif`, you need to compile the runtime library, once for
each image you use:

```bash
# host
docker run -it --rm -v "$(pwd)":/workspace -p 3001:3001 entropyverif:1.8

# container
cd entropy_verif/lib
make lib
cd ../..
```

### Equational theories

The equations the BC models use for key resizing are not subterm-convergent, so
tamarin-prover warns about it when a model is loaded. Subterm convergence is
sufficient for the finite variant property but not necessary, so `fvp/` checks
the property directly with fvpgen; see `fvp/README.md`.

### Case Studies

Models and analysis results for four real-world protocols are provided in `case_studies/wpa2`, `case_studies/bc`, `case_studies/ble`, `case_studies/pay`.

#### case_studies/bc

You can generate BC session models for various scenarios. This repository provides several scenarios mentioned in the paper. The commands for generating and verifying them are as follows:

```bash
# host
docker run -it --rm -v "$(pwd)":/workspace -p 3001:3001 entropyverif:1.8

# container
cd case_studies/bc

# one scenario
make BC_SESSION_MODELS/BC_SESSION_QA_CLEO_CEKS_PLEO_PLKS.spthy
python3 ./verifier.py

# both QA and SA scenarios
make all
python3 ./verifier.py

# inspect the results (replace <timestamp> with the directory)
tamarin-prover interactive result_<timestamp>/ --port=3001 --interface='*4' --derivcheck-timeout=0
```

`verifier.py` verifies models in parallel and nothing bounds the memory of a
single `tamarin-prover` invocation, so peak memory is roughly the number of
parallel jobs times the peak of one model. Use `--jobs` to lower it:

```bash
python3 ./verifier.py --jobs 4
```

A copy of our own run is archived in `case_studies/bc/results.zip`:

```bash
# container
cd case_studies/bc
unzip results.zip
tamarin-prover interactive results/ --port=3001 --interface='*4' --derivcheck-timeout=0
```

#### case_studies/ble

```bash
# host
docker run -it --rm -v "$(pwd)":/workspace -p 3001:3001 entropyverif:1.8

# container
python3 ./entropy_verif/main.py ./case_studies/ble/source/BLE_SC.spthy -o ./case_studies/ble/model/BLE_SC_generated.spthy --derive-level=2 --propagate-level=1

MODELFILE="./case_studies/ble/model/BLE_SC_generated.spthy"
OUTFILE="./case_studies/ble/result/BLE_SC_result.spthy"
export LC_ALL=C.UTF-8 && \
    tamarin-prover +RTS -N8 -RTS --derivcheck-timeout=0 $MODELFILE \
    --prove --stop-on-trace=SEQDFS --output=$OUTFILE > $OUTFILE.tmp \
    && echo "" >> $OUTFILE && cat $OUTFILE.tmp >> $OUTFILE && rm $OUTFILE.tmp

# inspect the archived results
tamarin-prover interactive ./case_studies/ble/result/ --port=3001 --interface='*4' --derivcheck-timeout=0
```

#### case_studies/wpa2

```bash
# host
docker run -it --rm -v "$(pwd)":/workspace -p 3001:3001 entropyverif:1.8

# container
python3 ./entropy_verif/main.py ./case_studies/wpa2/source/wpa2_four_way_handshake.spthy -o ./case_studies/wpa2/model/wpa2_four_way_handshake_generated.spthy --derive-level=3 --propagate-level=3

# inspect the archived results
tamarin-prover interactive ./case_studies/wpa2/results/ --port=3001 --interface='*4' --derivcheck-timeout=0
```

#### case_studies/pay

```bash
# host
docker run -it --rm -v "$(pwd)":/workspace -p 3001:3001 entropyverif:1.10

# container
cd case_studies/pay

# all scenarios
make all

# inspect the archived results
tamarin-prover interactive ./result/entropy --port=3001 --interface='*4' --derivcheck-timeout=0
```

`make all` verifies four models per condition. `alipay_order_code` carries the tactic of the
original model, and `alipay_order_code_tuned` adds one deprioritisation line to that tactic; the
line is present in both the baseline and the entropy version, so the pair differs only in the
low-entropy annotation. Results are in `result/baseline/` and `result/entropy/`, and each file
ends with the `summary of summaries` block reporting the verdicts and the processing time.
