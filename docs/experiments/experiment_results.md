# Experiment Results

This document summarizes the simulator experiments completed during the Q# onboarding project. It combines the introductory random-bit checkpoint with the final two-qubit Grover search experiments.

All results reported here come from the preserved artifacts under:

```text
results/raw/
results/processed/
results/figures/
```

The raw JSON files retain individual simulator outcomes. The processed JSON files were derived from those outcomes, and the SVG figures were generated from the measured summaries.

> **Scope:** these are results from the local ideal QDK simulator. They validate the implemented logic and the expected ideal-state behavior; they do not measure physical quantum hardware performance or demonstrate quantum speedup from simulator runtime.

---

## 1. Environment and provenance

The accepted runs were performed with:

```text
Python: 3.11.13
QDK:    1.31.0
Backend: QDK local simulator (qsharp.run default)
```

The random-bit checkpoint and the Grover suite were generated at different stages of the project, so they have different original development-repository commit identifiers.

### Random-bit run

```text
Experiment ID: FND-RBIT-001
Run ID:        FND-RBIT-001_20260826T000720165466Z
Git commit:    b419c1d7d07d958c737808c52b2640d2481aab5a
Git dirty:     false
Callable:      RandomBit.Main()
```

### Grover final suite

```text
Suite ID:      20260826T105700588731Z
Git commit:    f8b8179ccc794109401389b9eb4d9b6a74c2c0d7
Git dirty:     false
Callable:      Grover.RunGroverSearch(target, iterations)
```

The commit identifiers above belong to the original validated development repository from which this curated submission was exported. They are intentionally preserved in the raw metadata and may not resolve inside this clean submission repository.

---

# 2. Random-bit checkpoint — FND-RBIT-001

## Purpose

The random-bit experiment checks a basic consequence of applying a Hadamard gate to `|0⟩`:

\[
H|0\rangle = \frac{|0\rangle + |1\rangle}{\sqrt{2}}.
\]

A computational-basis measurement should therefore return `Zero` and `One` with equal theoretical probability:

\[
P(0)=P(1)=0.5.
\]

The Q# operation was executed for **1,000 simulator shots**.

## Frozen acceptance rule

Before the accepted run, each observed rate was required to fall inside the inclusive band:

```text
0.45 <= measured rate <= 0.55
```

This is an engineering checkpoint for finite-sample behavior, not a claim that a random run must produce exactly 500/500.

## Measured result

| Outcome | Count | Measured rate | Theory | Absolute deviation |
| --- | ---: | ---: | ---: | ---: |
| Zero | 510 | 51.0% | 50.0% | 1.0 percentage point |
| One | 490 | 49.0% | 50.0% | 1.0 percentage point |

Result:

```text
FND-RBIT-001: PASS
```

Both rates lie inside the frozen 45%–55% interval.

![Random-bit measurement distribution](../../results/figures/FND-RBIT-001_20260826T000720165466Z.svg)

### Interpretation

The observed `51% / 49%` split is consistent with the expected equal-probability distribution.

The important lesson is not that the simulator produced exactly 50/50—it did not—but that repeated preparation and measurement reveal the distribution associated with the quantum state.

---

# 3. Grover experiment suite

The final Grover suite contains three experiments:

| Experiment | Purpose | Final shots |
| --- | --- | ---: |
| `GRV-BASE-001` | one-target, one-iteration baseline | 1,000 |
| `GRV-TARGET-001` | verify all four target values | 1,000 |
| `GRV-ITER-001` | compare 0, 1, and 2 iterations | 3,000 |
| **Total** |  | **5,000** |

All three experiments share the same suite ID and generating commit.

---

# 4. Theory for the four-candidate search

The production search space contains four basis states:

```text
|00>  |01>  |10>  |11>
```

with one marked target.

For Grover search with `N = 4` and one marked state:

\[
\sin(\theta)=\frac{1}{\sqrt{4}}=\frac12,
\]

so:

\[
\theta=\frac{\pi}{6}.
\]

After `k` Grover iterations, the ideal target probability is:

\[
P_{\text{target}}(k)
=
\sin^2((2k+1)\theta).
\]

For the iteration counts studied here:

| Iterations | Ideal target probability |
| ---: | ---: |
| 0 | 25% |
| 1 | 100% |
| 2 | 25% |

This gives a clear experiment: the target should begin at the uniform probability, reach the optimum after one iteration, and return to the uniform target probability after the second iteration.

---

# 5. Baseline — GRV-BASE-001

## Configuration

```text
target = 2
iterations = 1
shots = 1000
```

Target `2` corresponds to logical basis state:

```text
|10>
```

using the project convention `q0 = MSB`, `q1 = LSB`.

## Frozen acceptance rule

The ideal baseline was treated as deterministic:

```text
all 1000 measured outcomes must equal target 2
```

No weaker “target dominates” threshold was used.

## Measured result

| Outcome | Count | Rate |
| ---: | ---: | ---: |
| 0 | 0 | 0.0% |
| 1 | 0 | 0.0% |
| **2** | **1000** | **100.0%** |
| 3 | 0 | 0.0% |

Theoretical target rate:

```text
100.0%
```

Measured target rate:

```text
100.0%
```

Absolute deviation:

```text
0.0
```

Result:

```text
GRV-BASE-001: PASS
```

![Grover one-iteration baseline](../../results/figures/grover/GRV-BASE-001_20260826T105700588731Z.svg)

### Interpretation

The one-iteration implementation reproduced the ideal four-candidate Grover baseline exactly for target `2`.

Because this is an ideal simulator result, the exact result is evidence of algorithm/circuit correctness under the simulator model—not evidence that a noisy physical device would produce 100% success.

---

# 6. Target-change regression — GRV-TARGET-001

## Purpose

The oracle is parameterized by a classical target integer. This experiment checks that changing the marked target does not require a different hard-coded oracle implementation.

## Configuration

```text
targets = [0, 1, 2, 3]
iterations = 1
shots per target = 250
total shots = 1000
```

## Frozen acceptance rule

For every target:

```text
all 250 outcomes must equal the configured target
```

## Measured result

| Target | Logical state | Correct / shots | Success rate | Theory |
| ---: | :---: | ---: | ---: | ---: |
| 0 | `|00>` | 250 / 250 | 100.0% | 100.0% |
| 1 | `|01>` | 250 / 250 | 100.0% | 100.0% |
| 2 | `|10>` | 250 / 250 | 100.0% | 100.0% |
| 3 | `|11>` | 250 / 250 | 100.0% | 100.0% |

Result:

```text
GRV-TARGET-001: PASS
```

![Grover target-change regression](../../results/figures/grover/GRV-TARGET-001_20260826T105700588731Z.svg)

### Interpretation

All four target values reached the same ideal one-iteration success behavior.

This supports two implementation properties:

1. the basis-state encoding `0..3 <-> |00>..|11>` is consistent;
2. the parameterized oracle correctly applies the target-specific phase marking for every candidate.

---

# 7. Iteration-count experiment — GRV-ITER-001

## Purpose

Grover search is an amplitude-rotation process. Applying the Grover iteration repeatedly does not monotonically increase target success.

This experiment directly compares the implemented search at:

```text
0 iterations
1 iteration
2 iterations
```

with target `2`.

## Configuration

```text
target = 2
shots per iteration = 1000
total shots = 3000
```

## Frozen acceptance rules

### One iteration

For `iterations = 1`:

```text
all 1000 outcomes must equal target 2
```

### Zero and two iterations

For `iterations = 0` and `iterations = 2`, theory predicts a uniform four-outcome distribution.

For each candidate, the accepted finite-sample band was:

```text
0.20 <= measured rate <= 0.30
```

The band was frozen before the final run.

It is intentionally broader than the exact theoretical rate of 25%, because 1,000 finite samples are expected to fluctuate.

---

## 7.1 Zero iterations

Measured counts:

| Outcome | Count | Rate | Theory |
| ---: | ---: | ---: | ---: |
| 0 | 234 | 23.4% | 25.0% |
| 1 | 263 | 26.3% | 25.0% |
| **2 (target)** | **259** | **25.9%** | **25.0%** |
| 3 | 244 | 24.4% | 25.0% |

Target success:

```text
259 / 1000 = 25.9%
```

Every candidate rate lies inside the frozen 20%–30% interval.

Result:

```text
iterations = 0: PASS
```

---

## 7.2 One iteration

Measured counts:

| Outcome | Count | Rate | Theory |
| ---: | ---: | ---: | ---: |
| 0 | 0 | 0.0% | 0.0% |
| 1 | 0 | 0.0% | 0.0% |
| **2 (target)** | **1000** | **100.0%** | **100.0%** |
| 3 | 0 | 0.0% | 0.0% |

Target success:

```text
1000 / 1000 = 100.0%
```

Result:

```text
iterations = 1: PASS
```

---

## 7.3 Two iterations

Measured counts:

| Outcome | Count | Rate | Theory |
| ---: | ---: | ---: | ---: |
| 0 | 261 | 26.1% | 25.0% |
| 1 | 245 | 24.5% | 25.0% |
| **2 (target)** | **229** | **22.9%** | **25.0%** |
| 3 | 265 | 26.5% | 25.0% |

Target success:

```text
229 / 1000 = 22.9%
```

Every candidate rate lies inside the frozen 20%–30% interval.

Result:

```text
iterations = 2: PASS
```

---

## Iteration comparison

| Iterations | Target successes | Target rate | Theory | Absolute deviation |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 259 / 1000 | 25.9% | 25.0% | 0.9 percentage point |
| 1 | 1000 / 1000 | 100.0% | 100.0% | 0.0 |
| 2 | 229 / 1000 | 22.9% | 25.0% | 2.1 percentage points |

![Grover iteration-count comparison](../../results/figures/grover/GRV-ITER-001_20260826T105700588731Z.svg)

Result:

```text
GRV-ITER-001: PASS
```

### Interpretation

The measured pattern matches the expected qualitative Grover behavior:

```text
approximately 25%
        ↓
100%
        ↓
approximately 25%
```

The result demonstrates why one iteration is optimal for this specific `N=4`, one-marked-target problem.

The second iteration does not represent an implementation failure. It deliberately shows the state rotating past the optimum.

The stochastic configurations do not need to equal exactly 25%. Their measured target rates of `25.9%` and `22.9%`, and all other candidate rates, remain within the frozen finite-sample acceptance band.

---

# 8. Observation versus interpretation

It is useful to separate what was **measured** from what is **inferred**.

## Direct observations

The preserved data directly show:

- random-bit outcomes: `510 Zero`, `490 One`;
- baseline Grover target `2`: `1000/1000`;
- one-iteration target regression: `250/250` for every target;
- iteration experiment target rates:
  - `25.9%` at `k=0`;
  - `100.0%` at `k=1`;
  - `22.9%` at `k=2`.

## Interpretation

Those observations are consistent with:

- equal measurement probabilities after preparing `H|0⟩`;
- exact ideal amplitude amplification after one Grover iteration for `N=4`;
- a single parameterized oracle working across all four logical targets;
- Grover's non-monotonic dependence on iteration count.

The interpretation depends on the ideal simulator model and the known theory of the fixed four-candidate circuit.

---

# 9. Evidence map

## Random-bit

Raw:

```text
results/raw/fundamentals/FND-RBIT-001_20260826T000720165466Z.json
```

Processed:

```text
results/processed/FND-RBIT-001_20260826T000720165466Z_summary.json
```

Figure:

```text
results/figures/FND-RBIT-001_20260826T000720165466Z.svg
```

## Grover baseline

Raw:

```text
results/raw/grover/GRV-BASE-001_20260826T105700588731Z.json
```

Processed:

```text
results/processed/grover/GRV-BASE-001_20260826T105700588731Z.json
```

Figure:

```text
results/figures/grover/GRV-BASE-001_20260826T105700588731Z.svg
```

## Grover target-change

Raw:

```text
results/raw/grover/GRV-TARGET-001_20260826T105700588731Z.json
```

Processed:

```text
results/processed/grover/GRV-TARGET-001_20260826T105700588731Z.json
```

Figure:

```text
results/figures/grover/GRV-TARGET-001_20260826T105700588731Z.svg
```

## Grover iteration count

Raw:

```text
results/raw/grover/GRV-ITER-001_20260826T105700588731Z.json
```

Processed:

```text
results/processed/grover/GRV-ITER-001_20260826T105700588731Z.json
```

Figure:

```text
results/figures/grover/GRV-ITER-001_20260826T105700588731Z.svg
```

---

# 10. Limitations

These experiments were intentionally limited to onboarding-scale ideal simulation.

They do not include:

- physical quantum hardware;
- device noise;
- decoherence;
- gate/readout error;
- hardware topology;
- compilation cost;
- resource estimation;
- scaling beyond the fixed two-qubit search;
- timing-based quantum/classical speedup comparison.

The experiments therefore support claims about **correctness and expected ideal simulator behavior** for the implemented circuit.

They do not establish real-device reliability, execution speed, or practical quantum advantage.

---

# 11. Summary

The experiment sequence builds from a simple probabilistic quantum measurement to a complete amplitude-amplification example:

```text
Random bit
50/50 expectation
measured 51/49
        ↓
Grover initial state
25% target probability
        ↓
one iteration
100% target probability
        ↓
second iteration
returns near 25%
```

Across the accepted data:

- the random-bit checkpoint passed its frozen finite-sample criterion;
- the one-iteration Grover baseline matched ideal theory exactly;
- all four target values passed without redesigning the oracle;
- the iteration-count study reproduced the expected non-monotonic success pattern;
- all final experiment acceptance rules passed.

Together, these results connect the project's central learning concepts—superposition, phase, interference, measurement, and repeated sampling—to concrete Q# behavior on the local ideal simulator.
