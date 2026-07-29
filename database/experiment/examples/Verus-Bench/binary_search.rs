//This example is from Verus tutorial, Chpt 7.5
use vstd::prelude::*;
fn main() {}

verus!{
fn binary_search(v: &Vec<u64>, k: u64) -> (r: usize)
    requires
        forall|i:int, j:int| 0 <= i <= j < v.len() ==> v[i] <= v[j],
        exists|i:int| 0 <= i < v.len() && k == v[i],
    ensures
        r < v.len(),
        k == v[r as int],
{
    let mut i1: usize = 0;
    let mut i2: usize = v.len() - 1;
    while i1 != i2
        invariant
            0 <= i1 <= i2 < v.len(),
            exists|i:int| i1 <= i < i2 + 1 && k == v[i],
            forall|i:int, j:int| 0 <= i <= j < v.len() ==> v[i] <= v[j],
        decreases
            i2 - i1
    {
        let ix = i1 + (i2 - i1) / 2;
        if v[ix] < k {
            proof {
                assert(exists|i:int| i1 <= i < i2 + 1 && k == v[i]);
                assert(forall|i:int, j:int| 0 <= i <= j < v.len() ==> v[i] <= v[j]);
                assert(v[ix as int] < k);
                assert(forall|i:int| i1 <= i <= ix ==> v[i] <= v[ix as int]);
                assert(forall|i:int| i1 <= i <= ix ==> v[i] < k);
                assert(forall|i:int| i1 <= i <= ix ==> v[i] != k);
                assert(exists|i:int| ix < i < i2 + 1 && k == v[i]);
            }
            i1 = ix + 1;
        } else {
            proof {
                assert(exists|i:int| i1 <= i < i2 + 1 && k == v[i]);
                assert(v[ix as int] >= k);
                if v[ix as int] == k {
                    assert(ix >= i1 && ix < i2 + 1);
                } else {
                    assert(v[ix as int] > k);
                    assert(forall|i:int, j:int| 0 <= i <= j < v.len() ==> v[i] <= v[j]);
                    assert(forall|i:int| ix <= i < i2 + 1 ==> v[ix as int] <= v[i]);
                    assert(forall|i:int| ix <= i < i2 + 1 ==> k < v[i]);
                    assert(forall|i:int| ix <= i < i2 + 1 ==> k != v[i]);
                    assert(exists|i:int| i1 <= i < ix && k == v[i]);
                }
            }
            i2 = ix;
        }
    }
    i1
}
}