namespace StatePreparationTests {
    import GroverProduction.Grover.PrepareUniformSuperposition;

    operation RunReversibleCheck() : Bool {
        use searchQubits = Qubit[2];

        PrepareUniformSuperposition(searchQubits);
        Adjoint PrepareUniformSuperposition(searchQubits);

        let q0Result = MResetZ(searchQubits[0]);
        let q1Result = MResetZ(searchQubits[1]);
        return q0Result == Zero and q1Result == Zero;
    }
}
