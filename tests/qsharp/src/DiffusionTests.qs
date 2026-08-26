namespace DiffusionTests {
    import GroverProduction.Grover.ApplyDiffusion;

    operation RunUniformEigenphaseCheck() : Bool {
        use searchQubits = Qubit[2];
        use probe = Qubit();

        // Prepare the uniform eigenstate |s> = H⊗2|00>.
        H(searchQubits[0]);
        H(searchQubits[1]);

        // Convert the diffuser's -1 eigenphase into probe result One.
        H(probe);
        Controlled ApplyDiffusion([probe], searchQubits);
        H(probe);

        let actual = MResetZ(probe);
        ResetAll(searchQubits);
        return actual == One;
    }

    operation RunOrthogonalEigenphaseCheck() : Bool {
        use searchQubits = Qubit[2];
        use probe = Qubit();

        // Prepare H⊗2|01> explicitly, with q1 as the logical LSB.
        X(searchQubits[1]);
        H(searchQubits[0]);
        H(searchQubits[1]);

        // Convert the orthogonal state's +1 eigenphase into probe result Zero.
        H(probe);
        Controlled ApplyDiffusion([probe], searchQubits);
        H(probe);

        let actual = MResetZ(probe);
        ResetAll(searchQubits);
        return actual == Zero;
    }

    operation RunEigenphaseChecks() : Bool {
        let uniformPass = RunUniformEigenphaseCheck();
        let orthogonalPass = RunOrthogonalEigenphaseCheck();
        return uniformPass and orthogonalPass;
    }
}
