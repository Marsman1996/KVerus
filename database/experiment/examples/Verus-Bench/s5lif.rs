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
		sum[0] == 6 * N,
{
	let mut i: usize = 0;
	sum.set(0, 0);

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
		forall|j: usize| j < i ==> a@[j as int] == 6,
		forall|j: usize| i <= j && j < N as usize ==> a@[j as int] == 1,
	decreases (N as usize - i)
	{
		if (a[i] == 1) {
			a.set(i, a[i] + 5);
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
		forall|j: usize| j < N as usize ==> a@[j as int] == 6,
		sum[0] == 6 * i as i32,
		N < 1000,
	decreases (N as usize - i)
	{
		assert(a@[i as int] == 6);
		assert(sum[0] + a@[i as int] == 6 * i as i32 + 6);
		assert(sum[0] + a@[i as int] == 6 * (i as i32 + 1));
		assert(i + 1 <= N as usize);
		sum.set(0, sum[0] + a[i]);
		i = i + 1;
	}
}
}