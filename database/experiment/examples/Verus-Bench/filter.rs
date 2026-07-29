use vstd::prelude::*;
fn main() {}

verus!{
pub fn myfun4(x: &Vec<u64>, y: &mut Vec<u64>)
requires 
    old(y).len() == 0,
ensures 
    y@ == x@.filter(|k: u64| k % 3 == 0),
{
    let mut i: usize = 0;
    let xlen = x.len();
    
    assert(y@.len() == 0);
    assert(x@.subrange(0 as int, 0 as int).filter(|k: u64| k % 3 == 0).len() == 0);
    
    while (i < xlen) 
    invariant
        i <= xlen,
        y@ == x@.subrange(0 as int, i as int).filter(|k: u64| k % 3 == 0),
        x@.len() == xlen as int,
    decreases
        xlen - i,
    { 
        if (x[i] % 3 == 0) {
            y.push(x[i]);
            assert(y@.last() == x@[i as int]);
            
            proof {
                let tmp1 = x@.subrange(0 as int, i as int).filter(|k: u64| k % 3 == 0);
                let tmp2 = seq![x@[i as int]];
                assert(y@ == tmp1 + tmp2);
            }
            
            assert(x@[i as int] % 3 == 0);
            assert(y@ == x@.subrange(0 as int, (i + 1) as int).filter(|k: u64| k % 3 == 0));
        } else {
            assert(x@[i as int] % 3 != 0);
            assert(y@ == x@.subrange(0 as int, i as int).filter(|k: u64| k % 3 == 0));
            
            assert(x@.subrange(0 as int, (i + 1) as int).filter(|k: u64| k % 3 == 0) == 
                   x@.subrange(0 as int, i as int).filter(|k: u64| k % 3 == 0)) by {
                assert(x@.subrange(0 as int, (i + 1) as int) == 
                       x@.subrange(0 as int, i as int) + seq![x@[i as int]]);
            }
        }
        i = i + 1;
    }
    
    assert(i == xlen);
    assert(x@.subrange(0 as int, xlen as int) == x@);
}
}