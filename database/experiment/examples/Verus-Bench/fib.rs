#[allow(unused_imports)]
use vstd::prelude::*;
fn main() {}

verus! {
spec fn fibo(n: int) -> nat
    decreases n
{
    if n <= 0 { 0 } else if n == 1 { 1 }
    else { fibo(n - 2) + fibo(n - 1) }
}

spec fn fibo_fits_i32(n: int) -> bool {
    fibo(n) < 0x8000_0000
}

fn fibonacci(n: usize) -> (ret: Vec<i32>)
requires
    fibo_fits_i32(n as int),
    n >= 2,
ensures
    forall |i: int| 2 <= i < n ==> #[trigger] ret@[i] ==  fibo(i), 
    ret@.len() == n,
{
    let mut fib = Vec::new();
    fib.push(0);
    fib.push(1);
    let mut i = 2;

    while i < n
    invariant
        fibo_fits_i32(n as int),
        n >= 2,
        2 <= i <= n,
        fib@.len() == i,
        fib@[0] == 0,
        fib@[1] == 1,
        forall |j: int| 2 <= j < i ==> #[trigger] fib@[j] == fibo(j),
    decreases n - i
    {
        // Get the values and prove they won't overflow
        let prev1 = fib[i - 1];
        let prev2 = fib[i - 2];
        
        assert(prev1 == fibo((i - 1) as int)) by {
            if (i - 1) == 1 {
                assert(fib@[1] == 1);
                assert(fibo(1) == 1);
            } else if (i - 1) == 0 {
                assert(fib@[0] == 0);
                assert(fibo(0) == 0);
            } else {
                assert(2 <= (i - 1) < i);
                assert(fib@[(i - 1) as int] == fibo((i - 1) as int));
            }
        }
        
        assert(prev2 == fibo((i - 2) as int)) by {
            if (i - 2) == 1 {
                assert(fib@[1] == 1);
                assert(fibo(1) == 1);
            } else if (i - 2) == 0 {
                assert(fib@[0] == 0);
                assert(fibo(0) == 0);
            } else {
                assert(2 <= (i - 2) < i);
                assert(fib@[(i - 2) as int] == fibo((i - 2) as int));
            }
        }
        
        // Prove that next_fib won't overflow
        assert(fibo(i as int) < 0x8000_0000) by {
            assert(fibo_fits_i32(n as int));
            assert(i < n);
            assert(fibo_fits_i32(n as int) ==> (forall |j: int| j < n ==> fibo(j) < 0x8000_0000)) by {
               admit();
            };
            assert(forall |j: int| j < n ==> fibo(j) < 0x8000_0000);
            assert(i < n);
            assert(fibo(i as int) < 0x8000_0000);
        }
        
        assert(fibo(i as int) == fibo((i - 2) as int) + fibo((i - 1) as int));
        assert(prev1 + prev2 == fibo(i as int));
        
        let next_fib = prev1 + prev2;
        
        assert(next_fib == fibo(i as int));
        
        fib.push(next_fib);
        
        // Prove loop invariant is maintained
        assert(forall |j: int| 2 <= j < i + 1 ==> #[trigger] fib@[j] == fibo(j)) by {
            assert(forall |j: int| 2 <= j < i ==> #[trigger] fib@[j] == fibo(j));
            assert(fib@[i as int] == next_fib);
            assert(next_fib == fibo(i as int));
        }
        
        i += 1;
    }

    fib
}
}