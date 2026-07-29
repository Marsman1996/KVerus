use vstd::prelude::*;

verus! {

fn incr_list(l: Vec<i32>) -> (result: Vec<i32>)
    requires
        forall|i: int| 0 <= i < l.len() ==> l[i] + 1 <= i32::MAX,  // avoid overflow

    ensures
        result.len() == l.len(),
        forall|i: int| 0 <= i < l.len() ==> #[trigger] result[i] == l[i] + 1,
{
    let mut result = Vec::with_capacity(l.len());
    for i in 0..l.len()
                                                                                                                                                                                                  
    {
        result.push(l[i] + 1);
    }
    result
}

} // verus!

fn main() {}
