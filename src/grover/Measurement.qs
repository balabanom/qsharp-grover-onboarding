namespace Grover {
    operation MeasureResult(searchQubits : Qubit[]) : Int {
        if Length(searchQubits) != 2 {
            fail "MeasureResult requires exactly two search qubits.";
        }

        // Measurement owns reset so callers can safely release the search register.
        let q0Result = MResetZ(searchQubits[0]);
        let q1Result = MResetZ(searchQubits[1]);

        // Decode q0 as the logical MSB and q1 as the logical LSB.
        if q0Result == Zero {
            if q1Result == Zero {
                return 0;
            }
            return 1;
        }

        if q1Result == Zero {
            return 2;
        }
        return 3;
    }

    export MeasureResult;
}
