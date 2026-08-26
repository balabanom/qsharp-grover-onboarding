namespace EntanglementDemo {
    operation Main() : (Result, Result) {
        use qubits = Qubit[2];

        // Put the control into superposition, then correlate the target with its basis state.
        H(qubits[0]);
        CNOT(qubits[0], qubits[1]);

        let first = MResetZ(qubits[0]);
        let second = MResetZ(qubits[1]);

        return (first, second);
    }
}
