operation Main() : Result {
    use q = Qubit();
    H(q);

    // Measure the prepared state and reset the qubit before its allocation ends.
    return MResetZ(q);
}
