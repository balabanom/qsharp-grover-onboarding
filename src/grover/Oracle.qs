namespace Grover {
    operation ApplyOracle(searchQubits : Qubit[], target : Int) : Unit is Adj + Ctl {
        if Length(searchQubits) != 2 {
            fail "ApplyOracle requires exactly two search qubits.";
        }
        if target < 0 or target > 3 {
            fail "ApplyOracle target must be in the range 0..3.";
        }

        let q0 = searchQubits[0];
        let q1 = searchQubits[1];

        // Normalize each zero target bit so the selected logical state becomes |11>.
        if target < 2 {
            X(q0);
        }
        if target % 2 == 0 {
            X(q1);
        }

        // Mark only the normalized |11> component with phase -1.
        CZ(q0, q1);

        // Undo normalization in reverse order to preserve every basis-state label.
        if target % 2 == 0 {
            X(q1);
        }
        if target < 2 {
            X(q0);
        }
    }

    export ApplyOracle;
}
