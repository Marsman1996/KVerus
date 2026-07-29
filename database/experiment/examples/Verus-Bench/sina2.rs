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
		forall |k:int| 0 <= k < N ==> a[k] == N + 1,
{
	let mut i: usize = 0;
	sum.set(0, 0);

	while (i < N as usize)
	invariant
		N > 0,
		a.len() == N as usize,
		sum.len() == 1,
		i <= N as usize,
		forall |k: int| 0 <= k < i ==> a[k] == 1,
	decreases
		N as usize - i
	{
		a.set(i, 1);
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
	invariant
		N > 0,
		a.len() == N as usize,
		sum.len() == 1,
		i <= N as usize,
		forall |k: int| 0 <= k < N ==> a[k] == 1,
		sum[0] == i as i32,
	decreases
		N as usize - i
	{
		sum.set(0, sum[0] + a[i]);
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
	invariant
		N > 0,
		a.len() == N as usize,
		sum.len() == 1,
		i <= N as usize,
		sum[0] == N,
		forall |k: int| 0 <= k < i ==> a[k] == N + 1,
		forall |k: int| i <= k < N ==> a[k] == 1,
		N + 1 <= i32::MAX, // Add this to prevent overflow
	decreases
		N as usize - i
	{
		a.set(i, a[i] + sum[0]);
		i = i + 1;
	}
}
}