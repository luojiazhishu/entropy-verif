# Finite variant property

Tamarin requires the equational theory of a model to have the finite variant
property (FVP). The equations the BC models use for key resizing are not
subterm-convergent, so Tamarin prints a warning about it when such a model is
loaded. Subterm convergence is a sufficient condition for FVP, not a necessary
one, so the warning does not by itself say that the theory is unsuitable.

This directory checks the property directly, with **fvpgen**, the prototype
accompanying V. Cheval and C. Fontaine, *Automatic verification of Finite
Variant Property beyond convergent equational theories*, CSF 2025
(<https://github.com/VincentCheval/fvpgen>).

## What is checked

`theories/bc.txt` is the fvpgen input for the BC theory. It holds the equations
declared in `case_studies/bc/templates/bc_session_{QA,SA}_template.m4`
(`SelectAU`, `SelectKS` and `resize`), together with the equation EntropyVerif
itself adds to every model it generates
(`entropy_verif/assets/functions_equations.spthy`):

```
decombine(combine(m1, m2)) = <m1, m2>
```

Tamarin's own `<_,_>` pairing is written `pair/2` in the fvpgen input, since
fvpgen has no built-in pairing symbol. Function symbols that appear in the
models but in no equation are free constructors and do not affect the property,
so they are omitted. The BC models also load Tamarin's `symmetric-encryption`
builtin, which is supported by Tamarin itself and is not part of what is checked
here.

## Result

fvpgen terminates and produces an `En`-convergent rewrite system of 801 rules,
which establishes FVP. The full output of our run is in `logs/bc.log`; the
relevant line is the last block:

```
The following rewrite system is En-convergent for E
  ...
```

## Reproducing

fvpgen needs OCaml and Maude 3.x, neither of which is part of the two
verification images, so this check runs outside them. With both on PATH:

```bash
cd fvp
make check
```

This clones fvpgen at the pinned commit `9ae60b2`, builds it, re-runs the check
and overwrites `logs/`. The log committed here was produced with that commit and
Maude 3.5.1.
