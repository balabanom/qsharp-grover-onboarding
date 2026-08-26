namespace Grover {
    operation PrepareUniformSuperposition(searchQubits : Qubit[]) : Unit is Adj + Ctl {
        if Length(searchQubits) != 2 {
            fail "PrepareUniformSuperposition requires exactly two search qubits.";
        }

        let q0 = searchQubits[0];
        let q1 = searchQubits[1];

        // Give each of the four logical candidates the same initial amplitude.
        H(q0);
        H(q1);
    }

    export PrepareUniformSuperposition;
}
