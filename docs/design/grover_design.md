# Grover Search Design

This document describes the design of the simulator-based Grover search mini-project implemented in Q#. The goal is to expose the core mechanics of Grover search clearly in a small, inspectable system rather than hide them behind a generalized library implementation.

The production problem is intentionally fixed to **four candidates**, represented by **two search qubits**, with **one marked target**.

## 1. Problem definition

The search space is:

```text
0, 1, 2, 3
```

The caller provides:

```text
target     ∈ {0,1,2,3}
iterations ≥ 0
```

The production operation is:

```qsharp
RunGroverSearch(target : Int, iterations : Int) : Int
```

The ideal onboarding baseline uses exactly one Grover iteration.

For four candidates with one marked target, one iteration is theoretically optimal and gives target probability 1 on the ideal simulator.

## 2. Logical qubit encoding

The production search register contains exactly two qubits:

```text
searchQubits[0] = q0 = logical most-significant bit
searchQubits[1] = q1 = logical least-significant bit
```

The mapping is explicit:

| Candidate | Logical basis state | q0 | q1 |
| ---: | :---: | :---: | :---: |
| 0 | `|00>` | 0 | 0 |
| 1 | `|01>` | 0 | 1 |
| 2 | `|10>` | 1 | 0 |
| 3 | `|11>` | 1 | 1 |

The classical decoder is:

```text
value = 2 × bit(q0) + bit(q1)
```

This mapping is defined by the project itself rather than by any simulator display-order convention.

## 3. Production structure

The Grover implementation is split into five focused operations:

```text
StatePreparation.qs  -> PrepareUniformSuperposition
Oracle.qs            -> ApplyOracle
Diffusion.qs         -> ApplyDiffusion
Measurement.qs       -> MeasureResult
GroverSearch.qs      -> RunGroverSearch
```

The complete data flow is:

```text
allocate |00>
     ↓
prepare uniform superposition
     ↓
apply target phase oracle
     ↓
apply diffusion
     ↓
measure + decode + reset
     ↓
return candidate integer
```

Repository source:

- [`StatePreparation.qs`](../../src/grover/StatePreparation.qs)
- [`Oracle.qs`](../../src/grover/Oracle.qs)
- [`Diffusion.qs`](../../src/grover/Diffusion.qs)
- [`Measurement.qs`](../../src/grover/Measurement.qs)
- [`GroverSearch.qs`](../../src/grover/GroverSearch.qs)

## 4. Uniform-superposition preparation

The preparation interface is:

```qsharp
PrepareUniformSuperposition(searchQubits : Qubit[]) : Unit is Adj + Ctl
```

Starting from the newly allocated state `|00>`, Hadamard is applied to both search qubits:

\[
H^{\otimes 2}|00\rangle
=
\frac{|00\rangle + |01\rangle + |10\rangle + |11\rangle}{2}.
\]

Each candidate therefore begins with:

```text
amplitude   = 1/2
probability = 1/4
```

No measurement occurs during state preparation.

The operation supports both `Adjoint` and `Controlled` functors so that it remains reversible and directly testable.

## 5. Parameterized phase oracle

The oracle interface is:

```qsharp
ApplyOracle(searchQubits : Qubit[], target : Int) : Unit is Adj + Ctl
```

Its intended basis-state behavior is:

\[
O_t|x\rangle =
\begin{cases}
-|x\rangle & x=t,\\
 |x\rangle & x\neq t.
\end{cases}
\]

The oracle therefore **marks the target by phase**. It does not:

- measure the search register;
- return the target;
- generate a classical random result;
- allocate a production ancilla.

### 5.1 Target normalization

Controlled-Z naturally contributes phase `-1` to `|11>`. To support all four targets with one oracle, the selected target is temporarily normalized to `|11>`.

| Target | Logical state | Temporary X operations before CZ |
| ---: | :---: | --- |
| 0 | `|00>` | `X(q0)`, `X(q1)` |
| 1 | `|01>` | `X(q0)` |
| 2 | `|10>` | `X(q1)` |
| 3 | `|11>` | none |

The oracle flow is:

```text
target bits
    ↓
X on each qubit whose target bit is 0
    ↓
selected basis state maps to |11>
    ↓
CZ(q0, q1)
    ↓
undo the temporary X operations
```

The X operations only relabel the target temporarily. After uncomputation, the basis labels are restored and only the target amplitude carries the relative phase flip.

### 5.2 Example: target 2

Target `2` corresponds to:

```text
|10>
```

To normalize it to `|11>`, only `q1` is flipped:

```text
|10>
  ↓ X(q1)
|11>
  ↓ CZ
-|11>
  ↓ X(q1)
-|10>
```

All non-target basis states return without the target phase mark.

## 6. Diffusion operator

The diffuser interface is:

```qsharp
ApplyDiffusion(searchQubits : Qubit[]) : Unit is Adj + Ctl
```

The implementation uses the explicit gate sequence:

```text
H H
X X
CZ
X X
H H
```

or:

\[
D =
H^{\otimes 2}
X^{\otimes 2}
CZ
X^{\otimes 2}
H^{\otimes 2}.
\]

For the uniform state

\[
|s\rangle =
\frac{|00\rangle + |01\rangle + |10\rangle + |11\rangle}{2},
\]

this implementation realizes:

\[
D = I - 2|s\rangle\langle s|.
\]

The commonly written textbook convention is:

\[
D_{\text{textbook}} = 2|s\rangle\langle s| - I.
\]

The two differ by an overall minus sign:

\[
D = -D_{\text{textbook}}.
\]

In the uncontrolled production circuit this difference is only a **global phase**, so it does not change computational-basis measurement probabilities.

The distinction matters in the component tests, because controlling the diffuser makes that phase relative to a probe branch and therefore observable.

## 7. One Grover iteration

One iteration is defined as:

```text
ApplyOracle(searchQubits, target)
        ↓
ApplyDiffusion(searchQubits)
```

The complete baseline is:

```text
|00>
  ↓ H⊗H
uniform superposition
  ↓ oracle
target phase marked
  ↓ diffusion
target amplitude amplified
  ↓ measurement
target candidate
```

The production operation keeps an `iterations` parameter so the same implementation can also be used to study what happens before and after the optimal iteration count.

## 8. Measurement and cleanup

The measurement interface is:

```qsharp
MeasureResult(searchQubits : Qubit[]) : Int
```

It performs three responsibilities:

1. measure `q0` and `q1` in the computational basis;
2. decode the pair into candidate `0..3`;
3. reset the qubits before release.

The mapping is:

| Measured state | Returned value |
| :---: | ---: |
| `|00>` | 0 |
| `|01>` | 1 |
| `|10>` | 2 |
| `|11>` | 3 |

The end-to-end lifecycle is therefore:

```text
RunGroverSearch
  ├─ validate classical inputs
  ├─ allocate q0, q1 in |00>
  ├─ prepare
  ├─ repeat oracle + diffusion
  ├─ MeasureResult
  │    ├─ measure
  │    ├─ decode
  │    └─ reset
  └─ release qubits + return Int
```

No measurement is inserted into the oracle or diffuser, because doing so would destroy the coherence required for interference.

## 9. Theoretical behavior for four candidates

For one marked state among `N = 4` candidates,

\[
\sin(\theta) = \frac{1}{\sqrt{4}} = \frac12,
\]

so

\[
\theta = \frac{\pi}{6}.
\]

After `k` Grover iterations, the ideal target probability is:

\[
P_{\text{target}}(k)
=
\sin^2((2k+1)\theta).
\]

For this fixed problem:

| Iterations | Theoretical target probability |
| ---: | ---: |
| 0 | 25% |
| 1 | 100% |
| 2 | 25% |

This is why the baseline uses one iteration.

It also gives a useful onboarding result: **more Grover iterations are not automatically better**. The state rotates toward the target amplitude and can rotate past the optimum.

## 10. Testing strategy

A major design goal was to test the quantum transformations themselves, not only the final returned integer.

The dedicated Q# test project is:

```text
tests/qsharp/
├── qsharp.json
└── src/
    ├── StatePreparationTests.qs
    ├── OracleTests.qs
    ├── DiffusionTests.qs
    ├── MeasurementTests.qs
    └── GroverTests.qs
```

### 10.1 State-preparation test

The preparation operation is checked reversibly:

```text
|00>
  ↓ PrepareUniformSuperposition
|s>
  ↓ Adjoint PrepareUniformSuperposition
|00>
```

The final result must be exactly `|00>`.

This checks the implemented reversible transformation rather than trying to infer exact uniformity from a small number of random measurements.

### 10.2 Why the oracle needs a phase-sensitive test

Suppose the oracle transforms:

```text
|x> -> -|x>
```

A direct computational-basis measurement cannot distinguish `|x>` from `-|x>` because:

\[
|+a|^2 = |-a|^2.
\]

A test that only measures the search qubits could therefore miss a broken phase oracle.

### 10.3 Controlled-interference oracle test

The oracle test introduces one **test-only phase probe**.

Conceptually:

```text
probe |0>
   ↓ H
probe |+>
   ↓ controlled oracle
relative phase appears if candidate == target
   ↓ H
measure probe
```

Expected result:

```text
candidate == target  -> probe = One
candidate != target  -> probe = Zero
```

The complete test covers all:

```text
4 targets × 4 candidate states = 16 deterministic cases
```

The probe is only test instrumentation. It is not a production search qubit or production ancilla.

### 10.4 Phase-sensitive diffusion test

The diffuser is tested through two known eigenstates.

For the uniform state:

```text
D|s> = -|s>
```

so the controlled-interference probe must reveal the `-1` eigenphase.

For an orthogonal state such as:

\[
H^{\otimes 2}|01\rangle,
\]

the preferred diffuser has eigenvalue `+1`.

These two checks verify the actual reflection structure and the chosen phase convention.

### 10.5 Measurement mapping test

Each of the four basis states is prepared directly and passed to `MeasureResult`.

Required mapping:

```text
|00> -> 0
|01> -> 1
|10> -> 2
|11> -> 3
```

This independently protects the q0-MSB/q1-LSB convention.

### 10.6 End-to-end baseline

For each target in `0..3`:

```text
RunGroverSearch(target, 1)
```

must return the target exactly on the ideal simulator.

The final delivery validation enforced **100 exact host shots per target**:

```text
target 0 -> 100 / 100
target 1 -> 100 / 100
target 2 -> 100 / 100
target 3 -> 100 / 100
```

This is a deterministic ideal-simulator correctness check, not a probabilistic threshold.

## 11. Experiment design

The implementation supports controlled experiments without changing the search-register design.

The final simulator study included:

### Baseline

```text
target = 2
iterations = 1
shots = 1000
```

Theoretical target probability:

```text
100%
```

### Target-change

```text
targets = 0,1,2,3
iterations = 1
250 shots per target
```

This checks that one parameterized oracle works across all four marked states.

### Iteration count

```text
target = 2
iterations = 0,1,2
1000 shots per iteration
```

Theoretical target probabilities:

```text
25%, 100%, 25%
```

Measured results and figures are documented separately in [`docs/experiments/experiment_results.md`](../experiments/experiment_results.md).

## 12. Design constraints and limitations

The onboarding design intentionally remains small and explicit.

It assumes:

- exactly two production search qubits;
- exactly four candidates;
- exactly one marked target;
- target supplied as a classical integer;
- local ideal QDK simulator;
- no production ancilla.

It does not implement:

- arbitrary search-register sizes;
- multiple marked states;
- a scalable predicate oracle;
- physical quantum hardware execution;
- noise or error mitigation;
- quantum error correction;
- resource estimation;
- hardware benchmarking.

The objective is to make the essential Grover mechanism directly inspectable:

```text
superposition
    +
phase marking
    +
interference
    =
amplitude amplification
```

That mechanism, rather than scalability or hardware performance, is the central design outcome of this onboarding project.
