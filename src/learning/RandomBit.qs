namespace RandomBit {
    @EntryPoint()
    operation Main() : Result {
        use q = Qubit();

        // Create an equal superposition so either computational-basis result can be measured.
        H(q);

        // Measure the prepared state and reset the qubit before its allocation ends.
        return MResetZ(q);
    }
}
