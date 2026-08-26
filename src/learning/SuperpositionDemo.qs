namespace SuperpositionDemo {
    operation MeasureSuperposition() : Result {
        use q = Qubit();

        // Create an equal superposition before observing the qubit in the computational basis.
        H(q);

        return MResetZ(q);
    }

    operation HadamardRoundTrip() : Result {
        use q = Qubit();

        // Applying H twice cancels the transformation and recovers the original |0> state.
        H(q);
        H(q);

        return MResetZ(q);
    }
}
