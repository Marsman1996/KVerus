#[allow(unused_imports)]
use vstd::prelude::*;

fn main() {}

verus!{
spec fn f(seq: Seq<u64>, i: int) -> bool {
    seq[i] == i + 2
}

fn get_element_check_property(arr: Vec<u64>, i: usize) -> (ret: u64)
    requires
        arr.len() > 0,
        0 < i < arr@.len(),
        forall |i: int| 0 <= i < arr@.len() ==> f(arr@, i),
    ensures
        ret == i + 2,
        ret == arr@[i as int],
{
    // We know that f(arr@, i as int) is true from the precondition
    assert(f(arr@, i as int));
    // Which means arr@[i as int] == i as int + 2
    assert(arr@[i as int] == i as int + 2);
    
    arr[i]
}
}