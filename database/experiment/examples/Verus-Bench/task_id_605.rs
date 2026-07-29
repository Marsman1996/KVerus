use vstd::prelude::*;

fn main() {}

verus! {

spec fn is_divisible(n: int, divisor: int) -> bool {
    (n % divisor) == 0
}

fn prime_num(n: u64) -> (result: bool)
    requires
        n >= 2,
    ensures
        result == (forall|k: int| 2 <= k < n ==> !is_divisible(n as int, k)),
{
    if n <= 1 {
        return false;
    }
    let mut index = 2;
    while index < n
        invariant
            n >= 2,
            2 <= index <= n,
            forall|k: int| 2 <= k < index ==> !is_divisible(n as int, k),
        decreases n - index,
    {
        if ((n % index) == 0) {
            assert(is_divisible(n as int, index as int));
            assert(2 <= index < n);
            assert(exists|k: int| 2 <= k < n && is_divisible(n as int, k));
            return false;
        }
        index += 1;
    }
    assert(index == n);
    assert(forall|k: int| 2 <= k < index ==> !is_divisible(n as int, k));
    true
}

} // verus!