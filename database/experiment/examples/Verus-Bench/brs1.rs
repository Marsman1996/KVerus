use vstd::prelude::*;
fn main() {}
verus!{
pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
	requires
		N > 0,
		old(a).len() == N as usize,
		old(sum).len() == 1,
	ensures
		sum[0] <= N,
{
	let mut i: usize = 0;
	while (i < N as usize)
	invariant
		N > 0,
		a.len() == N as usize,
		i <= N as usize,
		forall|j: usize| j < i && j < a.len() ==> a[j as int] == 1,
	decreases (N as usize - i)
	{
		if (i % 1 == 0) {
			a.set(i, 1);
		} else {
			a.set(i, 0);
		}
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
	invariant
		N > 0,
		sum.len() == 1,
		i <= N as usize,
		a.len() == N as usize,
		forall|j: usize| j < a.len() ==> a[j as int] == 1,
		i > 0 ==> sum[0] <= i as i32,
	decreases (N as usize - i)
	{
		if (i == 0) {
			sum.set(0, 0);
		} else {
			assert(i < a.len());
			assert(a[i as int] == 1);
			assert(sum[0] + a[i as int] <= i as i32 + 1);
			sum.set(0, sum[0] + a[i]);
		}
		i = i + 1;
	}
}
}