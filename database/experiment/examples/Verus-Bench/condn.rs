use vstd::prelude::*;
fn main() {}
verus!{
pub fn myfun(a: &mut Vec<i32>, N: i32, m: i32)
	requires
		N > 0,
		old(a).len() == N,
	ensures
		forall |k:int| 0 <= k < N ==> a[k] <= N,
{
	let mut i: usize = 0;

	while (i < N as usize)
	invariant
		0 <= i <= N as usize,
		a.len() == N as usize,
		forall |k: int| 0 <= k < i ==> a[k] == m,
	decreases
		N as usize - i,
	{
		a.set(i, m);
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
	invariant
		0 <= i <= N as usize,
		a.len() == N as usize,
		forall |k: int| 0 <= k < i ==> a[k] <= N,
	decreases
		N as usize - i,
	{
		if (a[i] < N) {
			a.set(i, a[i]);
		} else {
			a.set(i, N);
		}
		i = i + 1;
	}
}
}