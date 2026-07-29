use vstd::prelude::*;
fn main() {}
verus!{
pub fn myfun(a: &mut Vec<i32>, N: u32)
	requires
		N > 0,
		old(a).len() == N,
	ensures
		forall |k:int| 0 <= k < N ==> a[k] % 2 == N % 2,
{
	let mut i: usize = 0;

	while (i < N as usize)
	invariant
		0 <= i <= N as usize,
		a.len() == N as usize,
		forall |k:int| 0 <= k < i ==> a[k] == 0,
	decreases
		N as usize - i,
	{
		a.set(i, 0);
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
	invariant
		0 <= i <= N as usize,
		a.len() == N as usize,
		forall |k:int| 0 <= k < i ==> a[k] % 2 == N % 2,
	decreases
		N as usize - i,
	{
		if (N % 2 == 0) {
			a.set(i, 2 as i32);
			assert(a[i as int] % 2 == 0);
			assert(N % 2 == 0);
			assert(a[i as int] % 2 == N % 2);
		} else {
			a.set(i, 1 as i32);
			assert(a[i as int] % 2 == 1);
			assert(N % 2 == 1);
			assert(a[i as int] % 2 == N % 2);
		}
		i = i + 1;
	}
}
}