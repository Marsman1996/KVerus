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
            xs@.map(|i: int, x| i * x).subrange(1, i as int) =~= ret@.map_values(|x| x as int),
            1 <= i <= xs.len() <= u32::MAX,
    {
        proof {
            // Prove that the multiplication does not overflow
            vstd::arithmetic::mul::lemma_mul_upper_bound(
                xs[i as int] as int,
                u32::MAX as int,
                i as int,
                u32::MAX as int,
            );
            assert(u32::MAX * u32::MAX <= u64::MAX);
            assert((i as u64) * (xs[i as int] as u64) == i as int * xs[i as int]);
        }
        ret.push((i as u64) * (xs[i] as u64));

        let ghost prods = xs@.map(|i: int, x| i * x);
        assert(prods.subrange(1, i as int).push(prods.index(i as int)) =~= prods.subrange(
            1,
            i + 1 as int,
        ));

        i += 1;
    }
    assert(xs@.map(|i: int, x| i * x).subrange(1, i as int) =~= xs@.map(|i: int, x| i * x).skip(1));
    ret
}

} // verus!

fn main() {}
