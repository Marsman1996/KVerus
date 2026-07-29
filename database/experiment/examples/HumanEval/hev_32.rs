use vstd::arithmetic::div_mod::{
    lemma_fundamental_div_mod, lemma_fundamental_div_mod_converse,
};
use vstd::prelude::*;

verus! {

pub open spec fn mul(a: nat, b: nat) -> nat {
    a * b
}

/// Specification for what it means for d to divide a
pub open spec fn divides(factor: nat, candidate: nat) -> bool {
    exists|k: nat| mul(factor, k) == candidate
}

/// Helper function to prove a % b == 0 imples b divides a
proof fn lemma_mod_zero(a: nat, b: nat)
    requires
        a > 0 && b > 0,
        a % b == 0,
    ensures
        divides(b, a),
{
    lemma_fundamental_div_mod(a as int, b as int);
    assert(a == b * (a / b) + (a % b));
    assert(a == b * (a / b));
    assert(mul(b, (a / b) as nat) == a);
    assert(divides(b, a));
}

/// Helper function to prove b divides a imples a % b == 0
proof fn lemma_mod_zero_reversed(a: nat, b: nat)
    requires
        a > 0 && b > 0,
        divides(b, a),
    ensures
        a % b == 0,
{
    let k_wit = choose|k: nat| mul(b, k) == a;
    lemma_fundamental_div_mod_converse(a as int, b as int, k_wit as int, 0);
    lemma_fundamental_div_mod(a as int, b as int);
}

/// Helper function to prove everything is divided by one
proof fn lemma_one_divides_all()
    ensures
        forall|v: nat| divides(1 as nat, v),
{
    assert forall|v: nat| divides(1 as nat, v) by {
        assert(mul(1, v) == v);
    }
}

/// Implementation.
fn largest_divisor(n: u32) -> (ret: u32)
    requires
        n > 1,
    ensures
        divides(ret as nat, n as nat),
        ret < n,
        forall|k: u32| (0 < k < n && divides(k as nat, n as nat)) ==> ret >= k,
{
    let mut i = n - 1;
    while i >= 2
        invariant
            n > 1,
            1 <= i < n,
            forall|k: u32| i < k < n ==> !divides(k as nat, n as nat),
        decreases i,
    {
        if n % i == 0 {
            proof {
                lemma_mod_zero(n as nat, i as nat);
            }
            return i;
        }
        i -= 1;

        assert forall|k: u32| i < k < n implies !divides(k as nat, n as nat) by {
            if k == i + 1 {
                assert(n % k != 0);
                if divides(k as nat, n as nat) {
                    lemma_mod_zero_reversed(n as nat, k as nat);
                    assert(false);
                }
            }
        }
    }
    proof {
        lemma_one_divides_all();
    }
    1
}

} // verus!

fn main() {}
