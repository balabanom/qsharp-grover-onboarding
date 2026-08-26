# Learning Summary

This document summarizes the quantum-computing and Q# concepts practiced during the onboarding project and shows how they connect to the two-qubit Grover search implementation.

The emphasis is on the concepts that were directly used in code: qubits, measurement, superposition, phase, interference, controlled operations, entanglement, qubit lifecycle management, and the Q# programming model.

## 1. Qubits, basis states, and amplitudes

A classical bit has one definite value, `0` or `1`. A qubit is described by a quantum state such as

\[
|\psi\rangle = \alpha|0\rangle + \beta|1\rangle,
\]

where the complex amplitudes satisfy

\[
|\alpha|^2 + |\beta|^2 = 1.
\]

The computational-basis states for one qubit are `|0⟩` and `|1⟩`. For two qubits there are four basis states:

```text
|00>  |01>  |10>  |11>
```

This four-state space is exactly the search space used later in the Grover project.

The amplitudes themselves are not probabilities. If a state is measured in the computational basis, the probability of each result is the squared magnitude of its amplitude.

For example,

\[
\frac{|0\rangle + |1\rangle}{\sqrt{2}}
\]

gives equal probabilities for `0` and `1`.

## 2. Measurement and repeated simulator runs

Measurement converts quantum-state information into a classical result.

A single shot gives one outcome, so repeated preparation and measurement are needed to observe the probability distribution of a quantum state.

Measurement also changes the state. It is therefore not equivalent to a passive debugging read. This matters when testing phase-based operations: measuring too early can remove the coherence that later interference depends on.

The `RandomBit.qs` exercise demonstrated this experimentally by preparing `H|0⟩` and measuring it 1,000 times.

Accepted result:

| Outcome | Count | Rate |
| --- | ---: | ---: |
| Zero | 510 | 51.0% |
| One | 490 | 49.0% |

The result is consistent with the expected 50/50 computational-basis distribution of an equal superposition.

![Random-bit experiment](../../results/figures/FND-RBIT-001_20260826T000720165466Z.svg)

## 3. Superposition and the Hadamard gate

The Hadamard gate creates equal superpositions from computational-basis states:

\[
H|0\rangle = \frac{|0\rangle + |1\rangle}{\sqrt{2}},
\]

\[
H|1\rangle = \frac{|0\rangle - |1\rangle}{\sqrt{2}}.
\]

The learning exercises use this in two ways:

- [`RandomBit.qs`](../../src/learning/RandomBit.qs) prepares an equal superposition before measurement.
- [`SuperpositionDemo.qs`](../../src/learning/SuperpositionDemo.qs) also demonstrates the deterministic identity

\[
H^2 = I.
\]

Applying `H` twice returns the original `|0⟩` state. This is useful because it shows that quantum gates are transformations of amplitudes, not random classical instructions.

For the Grover search, applying `H` to both search qubits prepares

\[
\frac{|00\rangle + |01\rangle + |10\rangle + |11\rangle}{2},
\]

so all four candidates are represented before the oracle is applied.

## 4. Phase and interference

One of the most important concepts for the project is that two quantum states can have identical immediate measurement probabilities but still behave differently later because of phase.

For example,

\[
\frac{|0\rangle + |1\rangle}{\sqrt{2}}
\]

and

\[
\frac{|0\rangle - |1\rangle}{\sqrt{2}}
\]

both give 50/50 results if measured immediately in the computational basis. The difference is the relative sign of the `|1⟩` amplitude.

That relative phase becomes observable when amplitudes are recombined.

This leads to interference:

- amplitudes with compatible phase can reinforce;
- amplitudes with opposite phase can cancel.

Grover search uses this mechanism deliberately:

```text
uniform superposition
        ↓
phase mark the target
        ↓
diffusion / interference
        ↓
increase target amplitude
        ↓
measurement
```

Superposition alone is not the source of Grover's useful behavior. The key step is creating a phase difference and then converting that difference into amplitude amplification through interference.

## 5. Basic gates used in the project

### X

The Pauli-X gate exchanges the computational-basis states:

\[
X|0\rangle = |1\rangle,
\qquad
X|1\rangle = |0\rangle.
\]

In the Grover oracle, X gates are used to normalize a selected target basis state to `|11⟩` before applying the phase-marking operation.

### H

The Hadamard gate is used for:

- preparing uniform superposition;
- changing basis;
- implementing the diffusion transformation;
- interference-based phase tests.

### Z / controlled phase

A Z-type phase operation changes the sign of a selected amplitude without changing its immediate computational-basis probability.

This is the core idea behind the Grover oracle: the target is marked by phase rather than by returning it classically.

## 6. Controlled operations and entanglement

A controlled operation applies a target operation conditionally on the quantum state of a control qubit.

The standard example used in the learning exercises is CNOT.

[`EntanglementDemo.qs`](../../src/learning/EntanglementDemo.qs) starts from `|00⟩`, applies `H` to the first qubit, and then applies CNOT:

\[
|00\rangle
\rightarrow
\frac{|00\rangle + |10\rangle}{\sqrt{2}}
\rightarrow
\frac{|00\rangle + |11\rangle}{\sqrt{2}}.
\]

The final state is a Bell state.

When both qubits are measured in the computational basis, only the correlated pairs `00` and `11` are expected. The individual results are not predetermined, but the pair has a joint quantum correlation.

This exercise provides a concrete example of how a controlled gate can create a multi-qubit state that cannot be described as two independent single-qubit states.

## 7. Q# programming model

The onboarding exercises also introduced the practical Q# programming model.

### Operations and functions

A Q# `operation` can execute quantum instructions such as gate applications, measurement, allocation, and reset.

A Q# `function` is used for deterministic classical computation and cannot directly perform quantum operations.

### Qubit allocation

Qubits are allocated with `use`. For example:

```qsharp
use q = Qubit();
```

A newly allocated qubit starts in `|0⟩`.

### Measurement and reset

A qubit must be safely returned to `|0⟩` before release.

The learning exercises frequently use:

```qsharp
MResetZ(q)
```

which measures in the Z basis, returns a classical `Result`, and resets the qubit.

This made qubit lifecycle management part of each small example rather than an afterthought.

### Classical control around quantum operations

Q# combines quantum operations with ordinary classical logic such as:

- `let` and `mutable`;
- `if` / `else`;
- loops;
- integer parameters;
- classical return values.

This becomes important in `RunGroverSearch(target, iterations)`, where `target` and `iterations` are classical inputs controlling a quantum circuit.

## 8. Exercises completed

The learning phase is represented by four small executable Q# examples:

| Exercise | Main concept |
| --- | --- |
| [`HelloQuantum.qs`](../../src/learning/HelloQuantum.qs) | qubit allocation, Hadamard, measurement, reset |
| [`RandomBit.qs`](../../src/learning/RandomBit.qs) | repeated measurement of an equal superposition |
| [`SuperpositionDemo.qs`](../../src/learning/SuperpositionDemo.qs) | superposition and `H² = I` |
| [`EntanglementDemo.qs`](../../src/learning/EntanglementDemo.qs) | Bell-state preparation with `H` + `CNOT` |

These exercises were used as preparation for the final Grover mini-project rather than as isolated examples.

## 9. How the fundamentals connect to Grover search

The two-qubit Grover implementation combines the learning topics directly:

| Fundamental concept | Role in Grover search |
| --- | --- |
| Two-qubit basis states | represent candidates `0..3` |
| Hadamard / superposition | prepares all four candidates with equal amplitude |
| Phase | oracle marks the selected candidate |
| Controlled phase operation | implements two-qubit phase marking |
| Interference | converts the phase distinction into amplitude amplification |
| Measurement | converts the final state into a classical candidate |
| Qubit reset | safely releases the search register |
| Classical control | selects target and iteration count |

For the four-candidate / one-target problem, the ideal target probability follows

\[
P(k) = \sin^2((2k+1)\theta),
\qquad
\theta = \arcsin\left(\frac12\right) = \frac{\pi}{6}.
\]

Therefore:

```text
0 Grover iterations -> 25% target probability
1 Grover iteration  -> 100% target probability
2 Grover iterations -> 25% target probability
```

The simulator experiments later reproduced this expected pattern: approximately 25%, then 100%, then approximately 25%.

## 10. Key takeaways

The most important technical ideas carried into the final project are:

1. A qubit is described by amplitudes, not by a hidden classical bit value.
2. Measurement probabilities come from squared amplitude magnitudes.
3. Superposition creates multiple coherent computational paths, but useful quantum behavior depends on how their phases interact.
4. Relative phase can matter even when immediate measurement probabilities are unchanged.
5. Interference is the mechanism that allows Grover's phase marking to become measurable amplitude amplification.
6. Controlled gates can create genuinely multi-qubit behavior such as entanglement.
7. Measurement must be used carefully because it changes quantum state.
8. Q# requires explicit attention to qubit allocation, measurement, reset, and the boundary between quantum operations and classical control.
9. Testing a quantum component sometimes requires an interference-based test rather than direct measurement.
10. For a fixed search-space size, more Grover iterations are not automatically better; the state rotates toward and then past the optimum.

These concepts provide the foundation for the design, implementation, and interpretation of the Grover search project included in this repository.
