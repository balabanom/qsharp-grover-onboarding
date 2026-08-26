namespace Grover {
    operation ApplyDiffusion(searchQubits : Qubit[]) : Unit is Adj + Ctl {
        if Length(searchQubits) != 2 {
            fail "ApplyDiffusion requires exactly two search qubits.";
        }

        let q0 = searchQubits[0];
        let q1 = searchQubits[1];

        // Reflect about the frozen uniform state with eigenphase -1 on |s>.
        H(q0);
        H(q1);

        X(q0);
        X(q1);

        CZ(q0, q1);

        X(q0);
        X(q1);

        H(q0);
        H(q1);
    }

    export ApplyDiffusion;
}
