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
        invariant
            xs.len() <= u32::MAX,
            1 <= i <= xs.len(),
            ret@.map_values(|x| x as int) =~= xs@.map(|j: int, x| j * x).skip(1).take((i - 1) as int),
        decreases xs.len() - i,
    {
        proof {
            // Prove that the multiplication does not overflow
            vstd::arithmetic::mul::lemma_mul_upper_bound(
                xs[i as int] as int,
                u32::MAX as int,
                i as int,
                u32::MAX as int,
            );
            
            // Prove that the result fits in u64
            assert((i as int) * (xs[i as int] as int) <= (u32::MAX as int) * (u32::MAX as int));
            assert((u32::MAX as int) * (u32::MAX as int) < u64::MAX);
        }
        ret.push((i as u64) * (xs[i] as u64));

        proof {
            let ghost prods = xs@.map(|j: int, x| j * x);
            
            // Show that after the push, the invariant is maintained
            assert(ret@.drop_last().map_values(|x| x as int) =~= prods.skip(1).take((i - 1) as int));
            assert(ret@.last() == (i as int) * (xs[i as int] as int));
            assert(prods[i as int] == (i as int) * (xs[i as int] as int));
            assert(prods.skip(1).take(i as int) =~= prods.skip(1).take((i - 1) as int).push(prods[i as int]));
            assert(ret@.map_values(|x| x as int) =~= prods.skip(1).take(i as int));
        }

        i += 1;
    }
    ret
}

fn main() {}

} // verus!