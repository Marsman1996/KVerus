use vstd::prelude::*;
fn main() {}
verus!{
pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
	requires
		N > 0,
		old(a).len() == N,
		old(sum).len() == 1,
		N < 1000,
	ensures
		sum[0] == 2 * N,
{
	sum.set(0, 0);
	let mut i: usize = 0;
	while (i < N as usize)
	invariant
		N > 0,
		a.len() == N,
		sum.len() == 1,
		N < 1000,
		i <= N as usize,
		forall|j: int| 0 <= j < i as int ==> a@[j] == 2,
	decreases (N as usize - i)
	{
		a.set(i, 2);
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
	invariant
		N > 0,
		a.len() == N,
		sum.len() == 1,
		N < 1000,
		i <= N as usize,
		sum[0] == 2 * i as i32,
		forall|j: int| 0 <= j < N as int ==> a@[j] == 2,
	decreases (N as usize - i)
	{
		// Since we know a[i] is always 2 from the first loop
		sum.set(0, sum[0] + a[i]);
		i = i + 1;
	}
}
}