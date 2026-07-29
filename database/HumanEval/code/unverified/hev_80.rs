use vstd::prelude::*;

verus! {

pub open spec fn is_divisible(n: int, divisor: int) -> bool {
    (n % divisor) == 0
}

pub open spec fn is_prime(n: int) -> bool {
    if n < 2 {
        false
    } else {
        (forall|k: int| 2 <= k < n ==> !is_divisible(n as int, k))
    }
}

// Implementation following the ground-truth
// This function checks whether a given string length is prime
fn prime_length(str: &[char]) -> (result: bool)
    ensures
        result == is_prime(str.len() as int),
{
    if str.len() < 2 {
        return false;
    }
    for index in 2..str.len()
                                                                                                                                        
    {
        if ((str.len() % index) == 0) {
                                                                ;
            return false;
        }
    }
    true
}

} // verus!

fn main() {}
