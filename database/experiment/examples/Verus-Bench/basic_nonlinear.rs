use vstd::prelude::*;
use vstd::arithmetic::mul::lemma_mul_upper_bound;
fn main() {}

verus!{
     
proof fn bound_check(x: u32, y: u32)
    requires
        x <= 0xffff,
        y <= 0xffff,
    ensures
        x*y <= 0x100000000,
{
    // Convert to integers for easier mathematical reasoning
    let x_int: int = x as int;
    let y_int: int = y as int;
    
    // Establish that x and y are non-negative
    assert(x_int >= 0 && y_int >= 0);
    
    // Apply the upper bound lemma to prove that the product is bounded
    lemma_mul_upper_bound(x_int, 0x10000, y_int, 0x10000);
    
    // Now we have x*y <= 0x10000 * 0x10000 = 0x100000000
    assert(0x10000 * 0x10000 == 0x100000000);
    
    // Therefore, x*y <= 0x100000000
}
}