#[allow(unused_imports)]
use vstd::prelude::*;

fn main() {}

verus! {

spec fn arith_sum_int(i: nat) -> nat
    decreases i
{
    if i == 0 { 0 } else { i + arith_sum_int( (i - 1) as nat) }
}

fn compute_arith_sum(n: u64) -> (sum: u64)
    requires
        arith_sum_int(n as nat) < 10000,
    ensures
        arith_sum_int(n as nat) == sum,
{
    let mut i: u64 = 0;
    let mut sum: u64 = 0;
    while i < n
        invariant
            i <= n,
            sum == arith_sum_int(i as nat),
            arith_sum_int(n as nat) < 10000,
        decreases n - i,
    {
        assert(sum + (i + 1) < 10000) by {
            assert(arith_sum_int(i as nat) + (i + 1) == arith_sum_int((i + 1) as nat)) by {
                if i == 0 {
                    assert(arith_sum_int(0) + 1 == 0 + 1);
                    assert(arith_sum_int(1) == 1);
                } else {
                    assert(arith_sum_int(i as nat) == i + arith_sum_int((i - 1) as nat));
                    assert(arith_sum_int(i as nat) + (i + 1) == i + arith_sum_int((i - 1) as nat) + (i + 1));
                    assert(arith_sum_int(i as nat) + (i + 1) == (i + 1) + i + arith_sum_int((i - 1) as nat));
                    assert(arith_sum_int(i as nat) + (i + 1) == (i + 1) + arith_sum_int(i as nat));
                }
            }
            assert(arith_sum_int((i + 1) as nat) <= arith_sum_int(n as nat)) by {
                if i + 1 < n {
                    assert(i + 1 < n);
                    lemma_arith_sum_monotonic((i + 1) as nat, n as nat);
                } else if i + 1 == n {
                    assert(arith_sum_int((i + 1) as nat) == arith_sum_int(n as nat));
                }
            }
            
            if i + 1 < n {
                lemma_arith_sum_monotonic((i + 1) as nat, n as nat);
                assert(arith_sum_int((i + 1) as nat) < arith_sum_int(n as nat));
            }
            
            assert(sum + (i + 1) == arith_sum_int((i + 1) as nat));
            assert(arith_sum_int((i + 1) as nat) <= arith_sum_int(n as nat));
            assert(arith_sum_int(n as nat) < 10000);
        }
        i = i + 1;
        sum = sum + i;
    }
    sum
}

proof fn lemma_arith_sum_monotonic(a: nat, b: nat)
    requires a < b
    ensures arith_sum_int(a) < arith_sum_int(b)
    decreases b - a
{
    if a + 1 == b {
        assert(arith_sum_int(b) == b + arith_sum_int((b - 1) as nat));
        assert(arith_sum_int(b) == b + arith_sum_int(a));
        assert(b > 0);
        assert(arith_sum_int(b) > arith_sum_int(a));
    } else {
        lemma_arith_sum_monotonic(a, (b - 1) as nat);
        assert(arith_sum_int(a) < arith_sum_int((b - 1) as nat));
        assert(arith_sum_int(b) == b + arith_sum_int((b - 1) as nat));
        assert(arith_sum_int(b) > arith_sum_int((b - 1) as nat));
        assert(arith_sum_int(a) < arith_sum_int(b));
    }
}

} // verus!