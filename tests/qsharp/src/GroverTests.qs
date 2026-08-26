namespace GroverTests {
    import GroverProduction.Grover.RunGroverSearch;

    operation RunBaselineTargets() : Bool {
        for target in 0..3 {
            let actual = RunGroverSearch(target, 1);
            if actual != target {
                return false;
            }
        }
        return true;
    }
}
