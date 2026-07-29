//This is an example from Verus tutorial Chpt 4.2
//This is a rather complicated example

use vstd::prelude::*;
fn main() {}

verus!{
     
spec fn triangle(n: nat) -> nat
    decreases n
{
    if n == 0 {
        0
    } else {
        n + triangle((n - 1) as nat)
    }
}

fn tail_triangle(n: u32, idx: u32, sum: &mut u32)
    requires
        idx <= n,
        *old(sum) == triangle(idx as nat),
        triangle(n as nat) < 0x1_0000_0000,
    ensures
        *sum == triangle(n as nat),
    decreases n - idx
{
    if idx < n {
        let new_idx = idx + 1;
        
        proof {
            assert(*sum == triangle(idx as nat));
            assert(new_idx as nat == (idx as nat) + 1);
            assert(*sum as nat + new_idx as nat == triangle(idx as nat) + new_idx as nat);
            assert(triangle(new_idx as nat) == new_idx as nat + triangle((new_idx as nat - 1) as nat));
            assert(triangle(new_idx as nat) == new_idx as nat + triangle(idx as nat));
            assert(*sum as nat + new_idx as nat == triangle(new_idx as nat));
            
            // Prove that triangle is monotonically increasing
            lemma_triangle_monotonic(new_idx as nat, n as nat);
            
            assert(triangle(new_idx as nat) <= triangle(n as nat));
            assert(triangle(new_idx as nat) < 0x1_0000_0000);
        }
        
        let new_sum = *sum + new_idx;
        *sum = new_sum;
        tail_triangle(n, new_idx, sum);
    }
}

proof fn lemma_triangle_monotonic(i: nat, j: nat)
    requires i <= j
    ensures triangle(i) <= triangle(j)
    decreases j - i
{
    if i == j {
        assert(triangle(i) == triangle(j));
    } else {
        assert(j >= i + 1);
        lemma_triangle_monotonic(i, (j - 1) as nat);
        assert(triangle((j - 1) as nat) <= triangle(j));
    }
}
}