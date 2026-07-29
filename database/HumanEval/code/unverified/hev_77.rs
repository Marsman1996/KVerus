use vstd::prelude::*;

verus! {

#[verifier::memoize]
spec fn spec_fibfib(n: nat) -> nat
    decreases n,
{
    if (n == 0) {
        0
    } else if (n == 1) {
        0
    } else if (n == 2) {
        1
    } else {
        spec_fibfib((n - 1) as nat) + spec_fibfib((n - 2) as nat) + spec_fibfib((n - 3) as nat)
    }
}

proof fn lemma_fibfib_monotonic(i: nat, j: nat)
    requires
        i <= j,
    ensures
        spec_fibfib(i) <= spec_fibfib(j),
    decreases j - i,
{
    if (i < 3 && j < 3) || i == j {
    } else if i == j - 1 {
        reveal_with_fuel(spec_fibfib, 3);
        lemma_fibfib_monotonic(i, (j - 1) as nat);
    } else if i == j - 2 {
        reveal_with_fuel(spec_fibfib, 3);
        lemma_fibfib_monotonic(i, (j - 1) as nat);
        lemma_fibfib_monotonic(i, (j - 2) as nat);
    } else {
        lemma_fibfib_monotonic(i, (j - 1) as nat);
        lemma_fibfib_monotonic(i, (j - 2) as nat);
        lemma_fibfib_monotonic(i, (j - 3) as nat);
    }
}

fn fibfib(x: u32) -> (ret: Option<u32>)
    ensures
        match ret {
            None => spec_fibfib(x as nat) > u32::MAX,
            Some(f) => f == spec_fibfib(x as nat),
        },
{
    if x > 39 {
        proof {

        }
        return None;
    }
    match (x) {
        0 => Some(0),
        1 => Some(0),
        2 => Some(1),
        _ => {
            proof {

            }
            Some(fibfib(x - 1)? + fibfib(x - 2)? + fibfib(x - 3)?)
        },
    }
}

} // verus!

fn main() {}
