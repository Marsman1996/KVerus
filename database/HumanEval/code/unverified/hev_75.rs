use vstd::prelude::*;

verus! {

fn derivative(xs: &Vec<u32>) -> (ret: Vec<u64>)
    requires
        xs.len() <= u32::MAX,
    ensures
        if xs.len() == 0 {
            ret.len() == 0
        } else {
            ret@.map_values(|x| x as int) =~= xs@.map(|i: int, x| i * x).skip(1)
        },
{
    let mut ret = Vec::new();
    if xs.len() == 0 {
        return ret;
    }
    let mut i = 1;
    while i < xs.len()
                                                                                                                                                             
    {
        proof {
            // Prove that the multiplication does not overflow
            vstd::arithmetic::mul::lemma_mul_upper_bound(
                xs[i as int] as int,
                u32::MAX as int,
                i as int,
                u32::MAX as int,
            );
                                                   ;
                                                                                 ;
        }
        ret.push((i as u64) * (xs[i] as u64));

        let ghost prods = xs@.map(|i: int, x| i * x);
                                                                                                                                              ;

        i += 1;
    }
                                                                                                   ;
    ret
}

} // verus!

fn main() {}
