use vstd::prelude::*;
fn main() {}

verus!{
fn choose_odd()
{
    let mut idx: u64 = 0;
    let mut res: u64 = 5;
    while (idx < 10)
        invariant
            idx <= 10,
            res == 5 + idx,
        decreases 10 - idx,
    {
        res = res + 1;
        idx = idx + 1;
    }
    idx = 0;
    while (idx < 10)
        invariant
            idx <= 10,
            res == 15 + idx,
        decreases 10 - idx,
    {
        res = res + 1;
        idx = idx + 1;
    }
    assert(res == 25);
}
}