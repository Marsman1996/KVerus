use vstd::prelude::*;

verus! {

spec fn sum(s: Seq<i64>) -> int
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        s.last() + sum(s.drop_last())
    }
}

fn below_zero(operation: &[i64]) -> (r: bool)
    ensures
        r <==> !(forall|i: int|
            0 <= i <= operation.len() ==> sum(#[trigger] operation@.subrange(0, i)) >= 0),
{
    // We use i128 since it allows us to have sufficiently large numbers without overflowing.
    let mut s = 0i128;
    for i in 0usize..operation.len()
                                                                                                                                                                                                               
    {
                                                                                                                                          ;
        s = s + operation[i] as i128;
        if s < 0 {
            return true;
        }
    }
    false
}

} // verus!

fn main() {}
