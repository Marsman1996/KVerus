use vstd::prelude::*;

verus! {

spec fn spec_sum_to_n(n: nat) -> nat
    decreases n,
{
    if (n == 0) {
        0
    } else {
        n + spec_sum_to_n((n - 1) as nat)
    }
}

proof fn lemma_sum_monotonic(i: nat, j: nat)
    requires
        i <= j,
    ensures
        spec_sum_to_n(i) <= spec_sum_to_n(j),
    decreases j - i,
{
    if (i == 0 && j == 0) || i == j {
    } else if i == j - 1 {
        lemma_sum_monotonic(i, (j - 1) as nat);
    } else {
        lemma_sum_monotonic(i, (j - 1) as nat);
    }
}

proof fn lemma_sum_to_n_closed_form(n: nat)
    ensures
        spec_sum_to_n(n) == (n * (n + 1)) / 2,
    decreases n,
{
    if n == 0 {
    } else {
        assert(spec_sum_to_n((n - 1) as nat) == ((n - 1) * n) / 2) by {
            lemma_sum_to_n_closed_form((n - 1) as nat);
        }
        assert(n + (((n - 1) * n) / 2) == (n * (n + 1)) / 2) by (nonlinear_arith);
    }
}

fn sum_to_n(n: u32) -> (sum: Option<u32>)
    ensures
        match sum {
            None => spec_sum_to_n(n as nat) > u32::MAX,
            Some(f) => f == spec_sum_to_n(n as nat),
        },
{
    if n >= 92682 {
        proof {
            lemma_sum_to_n_closed_form(92682);
            lemma_sum_monotonic(92682, n as nat);
        }
        return None;
    }
    let mut res: u32 = 0;
    let mut sum: u32 = 0;
    let mut i: u32 = 0;
    while i < n
                                                                                                                      
    {
        i += 1;
        proof {
            // Prove that that n1 + n2 won't overflow
            lemma_sum_to_n_closed_form(92681);
            lemma_sum_monotonic(i as nat, 92681);
            lemma_sum_monotonic((i - 1) as nat, 92681);
        }
        res = i + res;
    }
    Some(res)
}

} // verus!

fn main() {}
