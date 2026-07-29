use vstd::prelude::*;
fn main() {}
verus!{

pub fn myfun(a: &mut Vec<u32>, N: u32) -> (sum: u32)
    requires 
        old(a).len() == N,
        N <= 0x7FFF_FFFF,
    ensures
        sum <= 2 * N,
{
    let mut i: usize = 0;
    while (i < N as usize)
        invariant
            i <= N as usize,
            a.len() == N,
            forall|j: int| 0 <= j < i as int ==> a@[j] <= 2,
        decreases N as usize - i,
    {
        if a[i] > 2 
        {
            a.set(i, 2);
        } 
        i = i + 1;
    }

    i = 0;
    let mut sum: u32 = 0;
    
    while (i < N as usize)
        invariant
            i <= N as usize,
            a.len() == N,
            forall|j: int| 0 <= j < N as int ==> a@[j] <= 2,
            sum <= 2 * i as u32,
            N <= 0x7FFF_FFFF,
        decreases N as usize - i,
    {
        assert(sum + a@[i as int] <= 2 * i as u32 + 2);
        assert(2 * i as u32 + 2 <= 2 * (i as u32 + 1));
        assert(sum + a@[i as int] <= 2 * (i as u32 + 1));
        assert(i < N as usize);
        assert(i < 0x7FFF_FFFF as usize);
        assert(sum <= 2 * i as u32);
        assert(a@[i as int] <= 2);
        assert(2 * i as u32 + 2 <= 0xFFFF_FFFF);
        sum = sum + a[i];
        i = i + 1;
    }

    sum
}
}