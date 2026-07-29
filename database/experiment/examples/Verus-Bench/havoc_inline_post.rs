use vstd::prelude::*;
fn main() {}
verus!{
pub fn havoc_inline_post(v: &mut Vec<u32>, a: u32, b: bool)
    requires 
        forall |k:int| 0 <= k < old(v).len() ==> old(v)[k] > 0,
        a > 0,
        b == false,
{  
    // Variables a and v are havocked. Their values are randomly reset, but their new values follow the following assumptions.
    assume(10 < a && a < 20);
    assume(forall |k:int| 0 <= k < v.len() ==> v[k] == 1);

    let c: bool = !b;
    let mut idx: usize = v.len();
    while (idx > 0)
        invariant
            forall |k:int| 0 <= k < v.len() ==> 
                if k >= idx { v[k] == 1 + a } else { v[k] == 1 },
            0 <= idx <= v.len(),
            a as u64 + 1 <= u32::MAX as u64,
        decreases idx,
    {
        idx = idx - 1;
        let val = v[idx];
        v.set(idx, val + a);
    }
    
    proof {  // inline postcondition
        assert(20 < 2*a && 2*a < 40);
        assert(forall |k:int| 0 <= k < v.len() ==> v[k] == 1 + a);
        assert(c == true);
    }
}
}