namespace MeasurementTests {
    import GroverProduction.Grover.MeasureResult;

    operation RunMappingChecks() : Bool {
        for candidate in 0..3 {
            use searchQubits = Qubit[2];

            // Prepare candidate = 2 * q0 + q1 using q0 as MSB and q1 as LSB.
            if candidate >= 2 {
                X(searchQubits[0]);
            }
            if candidate % 2 == 1 {
                X(searchQubits[1]);
            }

            let actual = MeasureResult(searchQubits);
            if actual != candidate {
                return false;
            }
        }
        return true;
    }
}
