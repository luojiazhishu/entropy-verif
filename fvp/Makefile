# ---------------------------------------------------------------------------
#  Finite variant property check for the equational theories used in the paper
#
#  Requirements (not part of the two verification images):
#    * OCaml    (ocamlopt, ocamlyacc, ocamllex)
#    * Maude 3.x, with the executable named `maude` on PATH
#      (fvpgen hardcodes the name and rejects Maude 2.x)
#
#    make check   build fvpgen at the pinned commit and re-run every theory,
#                 overwriting logs/
#    make clean   remove the fvpgen checkout
# ---------------------------------------------------------------------------

FVPGEN_REPO   := https://github.com/VincentCheval/fvpgen
FVPGEN_COMMIT := 9ae60b29e441a022d0426b05277d21d8432d0f42

THEORIES := bc

.PHONY: check clean

check: fvpgen/fvpgen
	@command -v maude >/dev/null 2>&1 || { echo "maude not found on PATH; fvpgen needs Maude 3.x under that exact name"; exit 1; }
	@mkdir -p logs
	@for t in $(THEORIES); do \
		echo "[FVP] $$t"; \
		./fvpgen/fvpgen theories/$$t.txt > logs/$$t.log 2>&1 \
			|| { echo "[FAIL] $$t, see logs/$$t.log"; exit 1; }; \
		grep -q '^The following rewrite system is En-convergent for E' logs/$$t.log \
			|| { echo "[FAIL] $$t: no En-convergent system produced"; exit 1; }; \
	done
	@echo "[OK] every theory admits an En-convergent rewrite system"

fvpgen/fvpgen:
	git clone $(FVPGEN_REPO) fvpgen
	cd fvpgen && git checkout --quiet $(FVPGEN_COMMIT) && $(MAKE)

clean:
	rm -rf fvpgen
