use vstd::prelude::*;
fn main() {}
verus!{
pub fn remove_all_greater(v: Vec<i32>, e: i32) -> (result: Vec<i32>)
    requires 
        forall |k1:int,k2:int| 0 <= k1 < k2 < v.len() ==> v[k1] != v[k2]
    ensures
        forall |k:int| 0 <= k < result.len() ==> result[k] <= e && v@.contains(result[k]),
        forall |k:int| 0 <= k < v.len() && v[k] <= e ==> result@.contains(v[k]),
{  
    let mut i: usize = 0;
    let vlen = v.len();
    let mut result: Vec<i32> = vec![];
    while (i < v.len()) 
        invariant
            forall |k1:int,k2:int| 0 <= k1 < k2 < v.len() ==> v[k1] != v[k2],
            i <= v.len(),
            forall |k:int| 0 <= k < result.len() ==> result[k] <= e && v@.contains(result[k]),
            forall |k:int| 0 <= k < i && v[k] <= e ==> result@.contains(v[k]),
        decreases v.len() - i,
    {  
        if (v[i] <= e) { 
            let ghost old_result = result@;
            result.push(v[i]);
            assert forall |k:int| 0 <= k < i && v[k] <= e implies result@.contains(v[k]) by {
                assert(old_result.contains(v[k]));
                assert(result@ == old_result.push(v[i as int]));
                let idx = old_result.index_of(v[k]);
                assert(result@[idx] == v[k]);
                assert(result@.contains(v[k]));
            }
            assert forall |k:int| 0 <= k < i + 1 && v[k] <= e implies result@.contains(v[k]) by {
                if k < i {
                    assert(result@.contains(v[k]));
                } else {
                    assert(k == i);
                    assert(result@ == old_result.push(v[i as int]));
                    assert(result@[result@.len() - 1] == v[i as int]);
                    assert(result@.contains(v[i as int]));
                }
            }
        } else {
            assert forall |k:int| 0 <= k < i + 1 && v[k] <= e implies result@.contains(v[k]) by {
                if k < i {
                    assert(result@.contains(v[k]));
                } else {
                    assert(k == i);
                    assert(v[i as int] > e);
                }
            }
        }
        i = i + 1;
    }  
    result
}
}