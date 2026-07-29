use vstd::prelude::*;

verus! {

// Note that according to the canonical solution 1 is treated as a possible largest prime. We'll stick to this
spec fn spec_prime_helper(num: int, limit: int) -> bool {
    forall|j: int| 2 <= j < limit ==> (#[trigger] (num % j)) != 0
}

spec fn spec_prime(num: int) -> bool {
    spec_prime_helper(num, num)
}

fn is_prime(num: u32) -> (result: bool)
    requires
        num >= 2,
    ensures
        result <==> spec_prime(num as int),
{
    let mut i = 2;
    let mut result = true;
    while i < num
        invariant
            num >= 2,
            2 <= i <= num,
            result ==> spec_prime_helper(num as int, i as int),
            !result ==> exists|k: int| 2 <= k < i && (#[trigger] (num as int % k)) == 0,
        decreases num - i,
    {
        if num % i == 0 {
            result = false;
        }
        i += 1;
    }
    assert(i == num);
    if result {
        assert(spec_prime_helper(num as int, num as int));
    } else {
        assert(exists|k: int| 2 <= k < num && (#[trigger] (num as int % k)) == 0);
        assert(!spec_prime(num as int));
    }
    result
}

fn largest_prime_factor(n: u32) -> (largest: u32)
    requires
        n >= 2,
    ensures
        1 <= largest <= n,
        spec_prime(largest as int),
        n % largest == 0,
        forall|p| 0 <= p < n && spec_prime(p) && n as int % p == 0 ==> p <= largest,
{
    let mut largest = 1;
    let mut j = 1;
    while j < n
        invariant
            n >= 2,
            1 <= j <= n,
            1 <= largest <= n,
            spec_prime(largest as int),
            n % largest == 0,
            forall|p| 0 <= p <= j && spec_prime(p) && n as int % p == 0 ==> p <= largest,
        decreases n - j,
    {
        j += 1;
        let flag = is_prime(j);
        if n % j == 0 && flag {
            largest =
            if largest > j {
                largest
            } else {
                j
            };
        }
    }
    assert(j == n);
    assert(forall|p| 0 <= p <= n && spec_prime(p) && n as int % p == 0 ==> p <= largest);
    assert(forall|p| 0 <= p < n && spec_prime(p) && n as int % p == 0 ==> p <= largest);
    largest
}

fn main() {}

} // verus!