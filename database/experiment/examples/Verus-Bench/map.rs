use vstd::prelude::*;
fn main() {}
verus!{
pub fn myfun2(x: &mut Vec<i32>) 
requires 
    forall |k:int| 0 <= k < old(x).len() ==> old(x)[k] <= 0x7FFF_FFFB,
ensures 
    x@.len() == old(x)@.len(),
    forall |k:int| 0 <= k < x.len() ==> #[trigger] x@[k] == old(x)@[k] + 4,
{
    let mut i: usize = 0;
    let xlen: usize = x.len();
    while (i < xlen) 
    invariant
        0 <= i <= xlen,
        xlen == x@.len(),
        xlen == old(x)@.len(),
        forall |k:int| 0 <= k < i ==> #[trigger] x@[k] == old(x)@[k] + 4,
        forall |k:int| i <= k < xlen ==> x@[k] == old(x)@[k],
        forall |k:int| 0 <= k < old(x).len() ==> old(x)[k] <= 0x7FFF_FFFB,
    decreases xlen - i,
    { 
        proof {
            assert(old(x)@[i as int] <= 0x7FFF_FFFB);
        }
        let val = x[i] + 4;
        x.set(i, val);  
        i = i + 1;
    }  
}
}