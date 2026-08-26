namespace Grover {
    operation RunGroverSearch(target : Int, iterations : Int) : Int {
        if target < 0 or target > 3 {
            fail "RunGroverSearch target must be in the range 0..3.";
        }
        if iterations < 0 {
            fail "RunGroverSearch iterations must be nonnegative.";
        }

        use searchQubits = Qubit[2];

        PrepareUniformSuperposition(searchQubits);

        for _ in 1..iterations {
            ApplyOracle(searchQubits, target);
            ApplyDiffusion(searchQubits);
        }

        // MeasureResult owns measurement and reset before this allocation is released.
        return MeasureResult(searchQubits);
    }

    export RunGroverSearch;
}
