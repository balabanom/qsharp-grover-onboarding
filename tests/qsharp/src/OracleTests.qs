namespace OracleTests {
    import GroverProduction.Grover.ApplyOracle;

    operation RunPhaseCase(target : Int, candidate : Int) : Bool {
        use searchQubits = Qubit[2];
        use probe = Qubit();

        // Prepare candidate = 2 * q0 + q1 using q0 as MSB and q1 as LSB.
        if candidate >= 2 {
            X(searchQubits[0]);
        }
        if candidate % 2 == 1 {
            X(searchQubits[1]);
        }

        // Convert the candidate's oracle eigenphase into a deterministic probe result.
        H(probe);
        Controlled ApplyOracle([probe], (searchQubits, target));
        H(probe);

        let actual = MResetZ(probe);
        ResetAll(searchQubits);

        if candidate == target {
            return actual == One;
        }
        return actual == Zero;
    }

    operation RunPhaseMatrix() : Bool {
        for target in 0..3 {
            for candidate in 0..3 {
                if not RunPhaseCase(target, candidate) {
                    return false;
                }
            }
        }
        return true;
    }
}
