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
		sum[0] == 4 * N,
{
	sum.set(0, 0);
	let mut i: usize = 0;
	while (i < N as usize)
	invariant
		N > 0,
		a.len() == N as usize,
		sum.len() == 1,
		i <= N as usize,
		forall|j: usize| j < i ==> a@[j as int] == 1,
	decreases (N as usize - i)
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
		forall|j: usize| j < i ==> a@[j as int] == 4,
		forall|j: usize| i <= j && j < N as usize ==> a@[j as int] == 1,
	decreases (N as usize - i)
	{
		if (a[i] == 1) {
			a.set(i, a[i] + 3);
		} else {
			a.set(i, a[i] - 1);
		}
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
	invariant
		N > 0,
		a.len() == N as usize,
		sum.len() == 1,
		i <= N as usize,
		forall|j: usize| j < N as usize ==> a@[j as int] == 4,
		sum[0] == (i as i32) * 4,
		N < 1000, // Added to ensure no overflow
	decreases (N as usize - i)
	{
		assert(a@[i as int] == 4);
		sum.set(0, sum[0] + a[i]);
		assert(sum[0] == (i as i32) * 4 + 4);
		assert(sum[0] == ((i + 1) as i32) * 4);
		i = i + 1;
	}
}
}